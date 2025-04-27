// main.go
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"sync"

	"proxyer/dto"
	"proxyer/provider"
	"strings"

	"github.com/gocraft/dbr/v2"
	_ "github.com/lib/pq"
	"gorm.io/gorm"
)

// Estrutura de resposta para o health-check
type healthResponse struct {
	Status string `json:"status"`
}

// Status representa o status do servidor
type Status string

// Handler do health-check
func healthHandler(w http.ResponseWriter, r *http.Request) {
	resp := healthResponse{Status: "ok"}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("Erro ao codificar resposta: %v", err)
	}
}

// Handler para capturar e salvar os dados no banco de dados
func newServerHandler(w http.ResponseWriter, r *http.Request, db *dbr.Session) {
	var input dto.ServerManagement
	// Decodifica o JSON recebido no corpo da requisição
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, "Erro ao decodificar JSON: "+err.Error(), http.StatusBadRequest)
		return
	}

	fromStruct, err := provider.MakeFieldMapFromStruct(&input, "json")
	if err != nil {
		return
	}

	fromStruct["uuid"], _ = provider.UUIDFromStruct(input)

	cols, rows := fromStruct.ToPair()

	// Insere o registro no banco de dados
	_, err = db.InsertInto("server_managements").
		Columns(cols...).
		Values(rows...).
		Exec()

	if err != nil {
		http.Error(w, "Erro ao salvar no banco de dados: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Retorna uma resposta de sucesso
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(fromStruct); err != nil {
		log.Printf("Erro ao codificar resposta: %v", err)
	}
}

type ErrorHandler struct {
	Message string `json:"message"`
}
type ServerLoader struct {
	servers map[string]*net.Listener
	conns   map[string][]net.Conn
	mu      sync.Mutex
}

// One2oneDialog represents a simples dialog with one request and one response

type One2oneDialog struct {
	Request  []byte
	Response []byte
}

type HttpDialogTranslatorFactory struct {
	RequestReader  bytes.Buffer
	ResponseReader bytes.Buffer
}

// InitMultiplexer analisa buffers e devolve canal com pares request/response.
func (dtf *HttpDialogTranslatorFactory) InitMultiplexer() <-chan One2oneDialog {
	out := make(chan One2oneDialog)

	go func() {
		defer close(out)

		reqBuf := bytes.NewReader(dtf.RequestReader.Bytes())
		resBuf := bytes.NewReader(dtf.ResponseReader.Bytes())

		reqReader := bufio.NewReader(reqBuf)
		resReader := bufio.NewReader(resBuf)

		for {
			// -------- decode request ----------
			req, err := http.ReadRequest(reqReader)
			if err == io.EOF {
				return // acabou tudo
			}
			if err != nil {
				return // erro inesperado
			}
			var rawReq bytes.Buffer
			req.Write(&rawReq) // inclui cabeçalho + body
			bodyLen := req.ContentLength
			if bodyLen > 0 {
				io.CopyN(&rawReq, reqReader, bodyLen)
			}
			req.Body.Close()

			// -------- decode response ----------
			// Precisa de um *fake* conn para ReadResponse
			resp, err := http.ReadResponse(resReader, req)
			if err != nil {
				return
			}
			var rawResp bytes.Buffer
			resp.Write(&rawResp)
			if resp.ContentLength > 0 {
				io.CopyN(&rawResp, resReader, resp.ContentLength)
			}
			resp.Body.Close()

			out <- One2oneDialog{
				Request:  rawReq.Bytes(),
				Response: rawResp.Bytes(),
			}
		}
	}()

	return out
}

func (dtf *HttpDialogTranslatorFactory) InitMocking(db *dbr.Session, buf *bytes.Buffer) (*bytes.Buffer, error) {
	reqBuf := bytes.NewReader(buf.Bytes())
	reqReader := bufio.NewReader(reqBuf)

	datagram, err := io.ReadAll(reqReader)
	if err != nil {
		return new(bytes.Buffer), nil
	}

	type DialogResult struct {
		Response []byte `db:"response"`
	}

	// [mock]
	// datagram = []byte("aloe")

	var response []DialogResult
	_, err = db.Select("response").
		From("server_simple_dialog").
		Where("request = ?", datagram).
		Load(&response)

	if err != nil {
		return new(bytes.Buffer), nil
	}

	return bytes.NewBuffer(response[0].Response), nil
}

func (sm *ServerLoader) CreateNewClientForSimpleRecord__V2(data dto.ServerManagement, uuid string, sess *dbr.Session) {
	sm.mu.Lock()
	if sm.servers == nil {
		sm.servers = make(map[string]*net.Listener)
		sm.conns = make(map[string][]net.Conn)
	}
	sm.mu.Unlock()

	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", int(data.PortProxy)))
	if err != nil {
		log.Printf("Error creating listener: %v", err)
		return
	}

	sm.mu.Lock()
	sm.servers[uuid] = &listener
	sm.mu.Unlock()

	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				if !strings.Contains(err.Error(), "use of closed network connection") {
					log.Printf("Error accepting connection: %v", err)
				}
				return
			}

			go func(netConnection net.Conn) {
				sm.mu.Lock()
				sm.conns[uuid] = append(sm.conns[uuid], netConnection)
				sm.mu.Unlock()

				defer func() {
					netConnection.Close()
					sm.mu.Lock()
					for i, conn := range sm.conns[uuid] {
						if conn == netConnection {
							sm.conns[uuid] = append(sm.conns[uuid][:i], sm.conns[uuid][i+1:]...)
							break
						}
					}
					sm.mu.Unlock()
				}()

				// 1. Lê tudo do cliente
				reqBuf := new(bytes.Buffer)
				if _, err := io.Copy(reqBuf, netConnection); err != nil {
					log.Printf("Erro lendo request: %v", err)
					return
				}

				var http HttpDialogTranslatorFactory

				// 2. Gera resposta com base na requisição lida
				resBuf, _ := http.InitMocking(sess, reqBuf)

				// 3. Escreve a resposta de volta no cliente
				if _, err := io.Copy(netConnection, resBuf); err != nil {
					log.Printf("Erro enviando response mock: %v", err)
					return
				}

				log.Printf("Request gravado:\n%s", reqBuf.String())
			}(conn)

		}
	}()
}

func (sm *ServerLoader) CreateNewClientForSimpleRecord(data dto.ServerManagement, uuid string, sess *dbr.Session) {
	sm.mu.Lock()
	if sm.servers == nil {
		sm.servers = make(map[string]*net.Listener)
		sm.conns = make(map[string][]net.Conn)
	}
	sm.mu.Unlock()

	listener, err := net.Listen("tcp", fmt.Sprintf(":%d", int(data.PortProxy)))
	if err != nil {
		log.Printf("Error creating listener: %v", err)
		return
	}

	sm.mu.Lock()
	sm.servers[uuid] = &listener
	sm.mu.Unlock()

	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				if !strings.Contains(err.Error(), "use of closed network connection") {
					log.Printf("Error accepting connection: %v", err)
				}
				return
			}

			go func(netConnection net.Conn) {
				sm.mu.Lock()
				sm.conns[uuid] = append(sm.conns[uuid], netConnection)
				sm.mu.Unlock()

				defer func() {
					err := netConnection.Close()
					if err != nil {
						return
					}
					sm.mu.Lock()
					for i, conn := range sm.conns[uuid] {
						if conn == netConnection {
							sm.conns[uuid] = append(sm.conns[uuid][:i], sm.conns[uuid][i+1:]...)
							break
						}
					}
					sm.mu.Unlock()
				}()

				target, err := net.Dial("tcp", fmt.Sprintf("localhost:%d", int(data.PortToBind)))
				if err != nil {
					log.Printf("Error connecting to target: %v", err)
					return
				}
				defer target.Close()

				var http HttpDialogTranslatorFactory

				// Buffer para armazenar os dados
				reqBuf := &http.RequestReader
				resBuf := &http.ResponseReader

				// Copia request do cliente para o target e armazena
				go func() {
					mw := io.MultiWriter(target, reqBuf)
					io.Copy(mw, netConnection)
					// Salvar request no banco
					log.Printf("RequestReader data: %s", reqBuf.String())
				}()

				// Copia response do target para o cliente e armazena
				mw := io.MultiWriter(netConnection, resBuf)
				io.Copy(mw, target)
				// Salvar response no banco
				log.Printf("ResponseReader data: %s", resBuf.String())

				chn := http.InitMultiplexer()

				// Assuma : chn é  chan One2oneDialog
				//         sess é *dbr.Session
				//         uuid é a FK do servidor que iniciou este proxy
				go func(ch <-chan One2oneDialog, sess *dbr.Session, fkUUID string) {
					for msg := range ch { // lê *todos* os diálogos que surgirem no canal

						var httpRequest msg.Request
						httpRequest.FromBytes(msg.Request)
						// struct temporária que será gravada
						content := struct {
							Request  []byte `json:"request"`
							Response []byte `json:"response"`
							UUID     string `json:"uuid"`
							FkUUID   string `json:"fk_uuid"`
						}{
							Request:  msg.Request,
							Response: msg.Response,
							FkUUID:   fkUUID,
						}

						// UUID determinístico/aleatório (string) para esta linha
						if uid, err := provider.UUIDFromStruct(content); err == nil {
							content.UUID = uid.String()
						}

						// converte struct → FieldMap → pares col/val
						fm, _ := provider.MakeFieldMapFromStruct(&content, "json")
						cols, vals := fm.ToPair()

						// INSERT na tabela server_simple_dialog
						if _, err := sess.
							InsertInto("server_simple_dialog").
							Columns(cols...).
							Values(vals...).
							Exec(); err != nil {

							log.Printf("erro ao inserir diálogo: %v", err)
						}
					}
				}(chn, sess, uuid) // <-- passa referências para a goroutine

			}(conn)
		}
	}()
}

func (sm *ServerLoader) RemoveClient(uuid string) {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if listener, ok := sm.servers[uuid]; ok {
		err := (*listener).Close()
		if err != nil {
			return
		}
		delete(sm.servers, uuid)

		// Close all active connections
		if conns, ok := sm.conns[uuid]; ok {
			for _, conn := range conns {
				err := conn.Close()
				if err != nil {
					return
				}
			}
			delete(sm.conns, uuid)
		}
	}
}

// Handler para capturar e salvar os dados no banco de dados
func switchServerHandler(w http.ResponseWriter, r *http.Request, db *dbr.Session, sm *ServerLoader) {
	var input dto.ServerSwitcher
	// Decodifica o JSON recebido no corpo da requisição
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, "Erro ao decodificar JSON: "+err.Error(), http.StatusBadRequest)
		return
	}

	if input.Type == "off-line" {
		sm.RemoveClient(input.Uuid)
	} else if input.Type == "simple-record" {
		var data dto.ServerManagement
		_, err := db.Select("*").From("server_managements").Where("uuid = ?", input.Uuid).Load(&data)
		if err != nil {
			return
		}
		sm.CreateNewClientForSimpleRecord(data, input.Uuid, db)
	} else if input.Type == "mocking" {
		var data dto.ServerManagement
		_, err := db.Select("*").From("server_managements").Where("uuid = ?", input.Uuid).Load(&data)
		if err != nil {
			return
		}
		sm.CreateNewClientForSimpleRecord__V2(data, input.Uuid, db)
	}

	sqlResult, err := db.Update("server_managements").
		Set("type", input.Type).
		Where("uuid = ?", input.Uuid).
		Exec()

	if err != nil {
		http.Error(w, "Erro ao salvar no banco de dados: "+err.Error(), http.StatusInternalServerError)
		return
	}

	nresult, _ := sqlResult.RowsAffected()

	if nresult == 0 {
		http.Error(w, "uuid não pode ser encontrado", http.StatusNotFound)
		w.WriteHeader(http.StatusOK)
		return
	}

	// Retorna uma resposta de sucesso
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
}

// Handler para capturar e salvar os dados no banco de dados
func listServerHandler(w http.ResponseWriter, r *http.Request, db *dbr.Session) {

	type Data struct {
		dto.ServerManagement
		Uuid string `json:"uuid"`
	}

	var content []Data
	// Insere o registro no banco de dados
	_, err := db.Select("*").
		From("server_managements").
		Load(&content)

	if err != nil {
		http.Error(w, "Erro ao salvar no banco de dados: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Retorna uma resposta de sucesso
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(content); err != nil {
		log.Printf("Erro ao codificar resposta: %v", err)
	}
}

// Handler para capturar e salvar os dados no banco de dados
func removeAllHandler(w http.ResponseWriter, r *http.Request, db *dbr.Session, sm *ServerLoader) {

	type Data struct {
		dto.ServerManagement
		Uuid string `json:"uuid"`
	}

	var content []Data
	// Insere o registro no banco de dados
	_, err := db.Select("*").
		From("server_managements").
		Load(&content)

	if err != nil {
		http.Error(w, "Erro ao salvar no banco de dados: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Retorna uma resposta de sucesso
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(content); err != nil {
		log.Printf("Erro ao codificar resposta: %v", err)
	}
}

func handlerMessage(w http.ResponseWriter, r *http.Request, db *gorm.DB) {
	resp := healthResponse{Status: "ok"}

	w.Header().Set("Content-Type", "application/json")

	if err := json.NewEncoder(w).Encode(resp); err != nil {
		log.Printf("Erro ao codificar resposta: %v", err)
	}

}

type EventReceiver struct{}

func (e EventReceiver) Event(eventName string) {
	//TODO implement me
	panic("implement me")
}

func (e EventReceiver) EventKv(eventName string, kvs map[string]string) {
	//TODO implement me
	panic("implement me")
}

func (e EventReceiver) EventErr(eventName string, err error) error {
	//TODO implement me
	panic("implement me")
}

func (e EventReceiver) EventErrKv(eventName string, err error, kvs map[string]string) error {
	//TODO implement me
	for k, v := range kvs {
		fmt.Printf("[%v] %v\n", k, v)
	}

	return err
}

func (e EventReceiver) Timing(eventName string, nanoseconds int64) {
	//TODO implement me
	panic("implement me")
}

func (e EventReceiver) TimingKv(eventName string, nanoseconds int64, kvs map[string]string) {
	//TODO implement me
	for k, v := range kvs {
		fmt.Printf("[%v] %v\n", k, v)
	}

}

func main() {

	// Registra a rota do health-check
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		healthHandler(w, r)
	})

	http.HandleFunc("/new", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		dsn := "host=localhost user=rickymal password=he147369 dbname=postgres port=12432 sslmode=disable"

		db, err := dbr.Open("postgres", dsn, nil)
		if err != nil {
			log.Fatal(err)
		}
		newServerHandler(w, r, db.NewSession(&EventReceiver{}))
	})

	http.HandleFunc("/list", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		dsn := "host=localhost user=rickymal password=he147369 dbname=postgres port=12432 sslmode=disable"

		db, err := dbr.Open("postgres", dsn, nil)
		if err != nil {
			log.Fatal(err)
		}
		listServerHandler(w, r, db.NewSession(&EventReceiver{}))
	})

	var sl ServerLoader

	http.HandleFunc("/update", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		dsn := "host=localhost user=rickymal password=he147369 dbname=postgres port=12432 sslmode=disable"

		db, err := dbr.Open("postgres", dsn, nil)
		if err != nil {
			log.Fatal(err)
		}
		switchServerHandler(w, r, db.NewSession(&EventReceiver{}), &sl)
	})

	http.HandleFunc("/remove-all", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		dsn := "host=localhost user=rickymal password=he147369 dbname=postgres port=12432 sslmode=disable"

		db, err := dbr.Open("postgres", dsn, nil)
		if err != nil {
			log.Fatal(err)
		}
		removeAllHandler(w, r, db.NewSession(&EventReceiver{}), &sl)
	})

	// Inicia o servidor HTTP
	addr := ":8081"
	log.Printf("Servidor iniciado em http://localhost%s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("Falha ao iniciar servidor: %v", err)
	}
}
