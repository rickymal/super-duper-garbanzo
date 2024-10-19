import http.server
import socketserver
import requests

# Porta em que o proxy vai rodar
PORT = 8080

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redireciona a requisição GET recebida para o endereço de destino
        target_url = f'http://192.168.1.10:8000{self.path}'  # IP do outro notebook
        print(f"Redirecionando requisição para: {target_url}")
        
        # Faz a requisição para o outro notebook
        response = requests.get(target_url)

        # Envia a resposta do outro notebook para o cliente original
        self.send_response(response.status_code)
        for header, value in response.headers.items():
            if header != 'Content-Length':
                self.send_header(header, value)
        self.end_headers()

        # Escreve o conteúdo da resposta
        self.wfile.write(response.content)

    def do_POST(self):
        # Lê os dados da requisição POST
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Redireciona para o notebook remoto
        target_url = f'http://192.168.1.10:8000{self.path}'  # IP do outro notebook
        print(f"Redirecionando POST para: {target_url}")
        
        # Envia o POST request para o servidor de destino
        response = requests.post(target_url, data=post_data, headers=self.headers)
        
        # Envia a resposta de volta ao cliente original
        self.send_response(response.status_code)
        for header, value in response.headers.items():
            self.send_header(header, value)
        self.end_headers()

        # Envia o conteúdo da resposta
        self.wfile.write(response.content)

# Configurando o servidor
with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
    print(f"Proxy HTTP rodando na porta {PORT}")
    httpd.serve_forever()
