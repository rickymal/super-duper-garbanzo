package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
	"strings"
)

// ======================
// STRATEGIES INTERFACES
// ======================

type Obrigado interface {
	DizerObrigado() string
}
type Filho struct {
	Obrigado
	Name string
}

type AAA struct{}

func (a AAA) DizerObrigado() string {
	return "obrigado"
}

var obj = Filho{
	Obrigado: AAA{},
}

// Struct alvo
type M struct{}

// Struct que embute M
type Parent struct {
	M
	FieldB int
}

// Struct que NÃO embute M
type AnotherStruct struct {
	FieldC string
}

// IsStructEmbedsM verifica se uma struct embute outra struct usando reflection
func IsStructEmbedsM(obj any, targetStruct any) bool {
	objType := reflect.TypeOf(obj)

	// Se for ponteiro, pegar o tipo subjacente
	if objType.Kind() == reflect.Ptr {
		objType = objType.Elem()
	}

	// Verifica se o tipo é uma struct
	if objType.Kind() != reflect.Struct {
		return false
	}

	targetType := reflect.TypeOf(targetStruct)

	// Itera pelos campos da struct
	for i := 0; i < objType.NumField(); i++ {
		field := objType.Field(i)

		// Verifica se o campo é embed (Anonymous) e se o tipo é igual ao alvo
		if field.Anonymous && field.Type == targetType {
			return true
		}
	}

	return false
}

// FilterStrategy define a regra para aceitar ou rejeitar determinado campo.
// Retorna true se o campo deve ser incluído, false caso contrário.
type FilterStrategy interface {
	Filter(fieldName string, fieldValue any, fieldTag reflect.StructTag) bool
}

// TransformStrategy define como modificar o valor de cada campo antes de exportar.
// Retorna o nome (potencialmente transformado) e o valor transformado.
type TransformStrategy interface {
	Transform(fieldName string, fieldValue any, fieldTag reflect.StructTag) (string, any)
}

// ExportStrategy define como o mapa resultante será exportado para algum formato
// (por exemplo, JSON, SQL, XML, etc.).
type ExportStrategy interface {
	Export(data map[string]any) ([]byte, error)
}

// =====================
// STRATEGIES EXEMPLO
// =====================

// ExampleFilterStrategy é um exemplo simples que filtra campos
// cujo valor seja vazio, zero ou nil.
type ExampleFilterStrategy struct{}

func (efs ExampleFilterStrategy) Filter(fieldName string, fieldValue any, fieldTag reflect.StructTag) bool {
	// Vamos supor que não queremos incluir campos vazios
	if fieldValue == nil {
		return false
	}
	switch v := fieldValue.(type) {
	case string:
		return v != ""
	case int, int64, float64:
		// Se numérico for zero, não inclui
		val := reflect.ValueOf(v).Int()
		return val != 0
	default:
		// Para qualquer outro tipo, incluindo struct aninhada, retorna true
		return true
	}
}

// ExampleTransformStrategy converte strings para maiúsculas, por exemplo.
type ExampleTransformStrategy struct{}

func (ets ExampleTransformStrategy) Transform(fieldName string, fieldValue any, fieldTag reflect.StructTag) (string, any) {
	switch v := fieldValue.(type) {
	case string:
		return fieldName, strings.ToUpper(v)
	default:
		return fieldName, fieldValue
	}
}

// ExampleJSONExportStrategy exporta o mapa para JSON.
type ExampleJSONExportStrategy struct{}

func (ejes ExampleJSONExportStrategy) Export(data map[string]any) ([]byte, error) {
	return json.MarshalIndent(data, "", "  ")
}

// ExampleSQLExportStrategy gera um SQL de INSERT como exemplo,
// assumindo a existência de uma tag `db:"nome_tabela"` na struct
type ExampleSQLExportStrategy struct{}

func (eses ExampleSQLExportStrategy) Export(data map[string]any) ([]byte, error) {
	// Precisaríamos saber o nome da tabela de alguma forma.
	// Uma das abordagens é ler do próprio map caso tenhamos armazenado
	// ou ler de uma tag associada ao struct. Aqui, vou supor que o nome
	// da tabela esteja armazenado na chave especial "_tableName".

	tableName, ok := data["_tableName"].(string)
	if !ok || tableName == "" {
		return nil, errors.New("não foi possível determinar o nome da tabela")
	}

	// Removemos a chave especial "_tableName" antes de montar o resto
	delete(data, "_tableName")

	cols := make([]string, 0, len(data))
	vals := make([]string, 0, len(data))

	for k, v := range data {
		cols = append(cols, k)
		switch val := v.(type) {
		case string:
			vals = append(vals, fmt.Sprintf("'%s'", val))
		case int, int64:
			vals = append(vals, fmt.Sprintf("%d", val))
		case float64:
			vals = append(vals, fmt.Sprintf("%f", val))
		default:
			// Usa a formatação padrão
			vals = append(vals, fmt.Sprintf("'%v'", val))
		}
	}

	query := fmt.Sprintf("INSERT INTO %s (%s) VALUES (%s);",
		tableName,
		strings.Join(cols, ", "),
		strings.Join(vals, ", "),
	)

	return []byte(query), nil
}

// =====================
// STRUCT HANDLER
// =====================

// StructHandler é o núcleo do nosso sistema
type StructHandler struct {
	Data any

	// Estratégias (opcionais) que podem ser definidas pelo usuário
	filter    FilterStrategy
	transform TransformStrategy
	export    ExportStrategy

	// Podemos armazenar outras estratégias conforme necessário, ex.: validação
}

// NewStructHandler é o construtor básico que recebe qualquer struct ou ponteiro para struct.
func NewStructHandler(data any) *StructHandler {
	return &StructHandler{
		Data: data,
	}
}

// WithFilterStrategy define a estratégia de filtro
func (sh *StructHandler) WithFilterStrategy(fs FilterStrategy) *StructHandler {
	sh.filter = fs
	return sh
}

// WithTransformStrategy define a estratégia de transformação
func (sh *StructHandler) WithTransformStrategy(ts TransformStrategy) *StructHandler {
	sh.transform = ts
	return sh
}

// WithExportStrategy define a estratégia de exportação
func (sh *StructHandler) WithExportStrategy(es ExportStrategy) *StructHandler {
	sh.export = es
	return sh
}

// ToMap converte a struct em um map[string]any
// aplicando Filter e Transform caso estejam configurados.
func (sh *StructHandler) ToMap() (map[string]any, error) {
	if sh.Data == nil {
		return nil, errors.New("Data is nil")
	}

	// Usa reflection para percorrer todos os campos
	val := reflect.ValueOf(sh.Data)
	typ := reflect.TypeOf(sh.Data)

	// Se for ponteiro, obtemos o elemento subjacente
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
		typ = typ.Elem()
	}

	if val.Kind() != reflect.Struct {
		return nil, fmt.Errorf("ToMap: tipo inválido (%s), esperado struct ou ponteiro para struct", val.Kind())
	}

	result := make(map[string]any)
	err := sh.extractFields(val, typ, result)
	if err != nil {
		return nil, err
	}

	return result, nil
}

// extraímos recursivamente os campos da struct, aplicando estratégias se existirem
func (sh *StructHandler) extractFields(v reflect.Value, t reflect.Type, result map[string]any) error {
	for i := 0; i < v.NumField(); i++ {
		fieldVal := v.Field(i)
		fieldType := t.Field(i)
		fieldName := fieldType.Name
		fieldTag := fieldType.Tag

		// Ignoramos campos não exportados (que começam com letra minúscula) ou
		// que tenham um tag de struct que indiquem omissão, se for do seu interesse.
		if !fieldVal.CanInterface() {
			continue
		}

		// Lê valor "cru"
		rawValue := fieldVal.Interface()

		// Se houver filterStrategy, aplicamos
		if sh.filter != nil {
			if !sh.filter.Filter(fieldName, rawValue, fieldTag) {
				continue
			}
		}

		// Se o campo for outra struct (e não do tipo time.Time, por exemplo),
		// podemos chamar recursivamente. Aqui simplificamos a verificação
		// dizendo que se for struct, mas não tempo, vamos entrar recursivamente.
		if fieldVal.Kind() == reflect.Struct && fieldType.Type.String() != "time.Time" {
			nestedResult := make(map[string]any)
			err := sh.extractFields(fieldVal, fieldType.Type, nestedResult)
			if err != nil {
				return err
			}

			// Aplicar transform em nível de "objeto aninhado" não faz muito sentido
			// em cada campo, mas podemos pensar num design alternativo.
			if len(nestedResult) > 0 {
				if sh.transform != nil {
					// Caso queira transformar nomes de campo "pai" para algo mais...
					// mas normalmente você transformaria cada campo lá dentro.
				}
				result[fieldName] = nestedResult
			}
			continue
		}

		// Se houver transformStrategy, aplicamos
		transformedName := fieldName
		transformedValue := rawValue
		if sh.transform != nil {
			tn, tv := sh.transform.Transform(fieldName, rawValue, fieldTag)
			transformedName = tn
			transformedValue = tv
		}

		// Armazenamos o valor no map
		result[transformedName] = transformedValue
	}
	return nil
}

// ToExport gera a saída ([]byte) usando a ExportStrategy definida
func (sh *StructHandler) ToExport() ([]byte, error) {
	if sh.export == nil {
		return nil, errors.New("nenhuma estratégia de exportação definida")
	}

	dataMap, err := sh.ToMap()
	if err != nil {
		return nil, err
	}

	// Por exemplo, se quisermos suportar SQL e precisarmos de uma tag da struct
	// para descobrir o nome da tabela, poderíamos inserir manualmente essa informação:
	// (Isso depende muito do seu design e como você extrai o nome da tabela.)
	if tableName, err := sh.getTableName(); err == nil && tableName != "" {
		dataMap["_tableName"] = tableName
	}

	return sh.export.Export(dataMap)
}

// getTableName é um exemplo de como você pode obter o nome da tabela
// a partir de uma tag da struct principal, por exemplo `db:"users"`.
func (sh *StructHandler) getTableName() (string, error) {
	if sh.Data == nil {
		return "", errors.New("Data is nil")
	}

	val := reflect.ValueOf(sh.Data)
	typ := reflect.TypeOf(sh.Data)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
		typ = typ.Elem()
	}
	if val.Kind() != reflect.Struct {
		return "", fmt.Errorf("getTableName: tipo inválido: %s", val.Kind())
	}

	tag := typ.Field(0).Tag.Get("db") // Exemplo, assumindo que o campo 0 tenha a tag do nome da tabela
	return tag, nil
}

// ===============
// EXEMPLO DE USO
// ===============

// User é um exemplo de struct que poderíamos querer manipular.
type User struct {
	// Supondo que colocamos o nome da tabela na tag db do primeiro campo.
	// É apenas um exemplo. Você pode modelar como quiser.
	TablePlaceholder string `db:"users"`
	ID               int
	Name             string
	Email            string
	Profile          Profile
}

// Profile é um exemplo de struct aninhada
type Profile struct {
	Bio   string
	Age   int
	Score float64
}

func main() {
	user := User{
		TablePlaceholder: "qualquer_valor",
		ID:               0,
		Name:             "João da Silva",
		Email:            "joao@example.com",
		Profile: Profile{
			Bio:   "Golang developer",
			Age:   30,
			Score: 42.5,
		},
	}

	app := AppManager{}
	

	go serviceA(app)
	go serviceB(app)
	go serviceC(app)

	var msg MessageContent
	select {
	case app.received(enum.ENCERRAMENTO_POD):
		app.finish()
	case msg = app.received(enum.ERRO_NO_HANDLE):
		etc ...
		app.stop()
	}

	// Criamos o StructHandler
	handler := NewStructHandler(user).
		WithFilterStrategy(ExampleFilterStrategy{}).
		WithTransformStrategy(ExampleTransformStrategy{}).
		WithExportStrategy(ExampleJSONExportStrategy{})

	// Geramos um map
	resultMap, err := handler.ToMap()
	if err != nil {
		panic(err)
	}
	fmt.Println("==== Mapa Gerado ====")
	for k, v := range resultMap {
		fmt.Printf("%s: %#v\n", k, v)
	}

	// Exportamos para JSON
	jsonBytes, err := handler.ToExport()
	if err != nil {
		panic(err)
	}
	fmt.Println("\n==== JSON Export ====")
	fmt.Println(string(jsonBytes))

	// Supondo que queremos agora exportar para SQL:
	handler = handler.WithExportStrategy(ExampleSQLExportStrategy{})
	sqlBytes, err := handler.ToExport()
	if err != nil {
		panic(err)
	}
	fmt.Println("\n==== SQL Export ====")
	fmt.Println(string(sqlBytes))
}
