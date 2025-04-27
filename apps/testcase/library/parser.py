def create_tcp_ip_server_proxy(self) -> None:
    """
    Create a TCP/IP server proxy that listens for incoming connections
    and handles them using the provided binary facades.
    """
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.bind((self.source, self.port))
    self.server_socket.listen(5)
    print(f"Server listening on {self.source}:{self.port}")

    try:
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection from {client_address}")
            handler_thread = threading.Thread(
                target=self.handle_client, args=(client_socket,)
            )
            handler_thread.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        self.server_socket.close()

def handle_client(self, client_socket: socket.socket) -> None:
    try:
        # Conecta com o servidor real
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((self.dest_host, self.dest_port))

        # Inicia threads para comunicação bidirecional
        threading.Thread(target=self.pipe, args=(client_socket, server_socket, "client")).start()
        threading.Thread(target=self.pipe, args=(server_socket, client_socket, "server")).start()

    except Exception as e:
        print(f"Proxy error: {e}")
        client_socket.close()
        if 'server_socket' in locals():
            server_socket.close()

def pipe(self, src_socket: socket.socket, dst_socket: socket.socket, direction: str) -> None:
    """
    Redireciona dados entre os sockets e passa para o facade.
    `direction` = "client" ou "server"
    """
    try:
        while True:
            data = src_socket.recv(4096)
            if not data:
                break

            # Intercepta o binário
            for facade in self.binary_facades:
                if direction == "client":
                    facade.on_client_data_received(data)
                else:
                    facade.on_server_data_received(data)

            dst_socket.sendall(data)

    except Exception as e:
        print(f"Pipe error ({direction}): {e}")
    finally:
        src_socket.close()
        dst_socket.close()
