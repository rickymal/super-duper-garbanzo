import asyncio
import socket

class ProxyServer:
    def __init__(self, original_port, mirror_port, binary_facades=None, host="localhost"):
        self.original_port = original_port
        self.mirror_port = mirror_port
        self.binary_facades = binary_facades or []
        self.host = host
        self.event_loop = asyncio.get_running_loop()

    async def stop(self):
        self.server_socket.close()

    async def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.original_port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)  # MUITO IMPORTANTE no asyncio
        
        print(f"Server listening on {self.host}:{self.original_port}")

        tasks = []
        try:
            while True:
                client_socket, client_address = await self.event_loop.sock_accept(self.server_socket)
                print(f"Connection from {client_address}")
                task = asyncio.create_task(self.handle_client(client_socket))
                tasks.append(task)
                tasks = [t for t in tasks if not t.done()]
        except asyncio.CancelledError:
            print("Server shutting down...")
        finally:
            self.server_socket.close()

    async def handle_client(self, client_socket: socket.socket) -> None:
        try:
            await asyncio.get_event_loop().sock_connect(server_socket, (self.host, self.mirror_port))
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setblocking(False)
            await asyncio.get_event_loop().sock_connect(server_socket, (self.mirror_port, self.port))

            # Agora rodamos os dois pipes em paralelo
            client_to_server = asyncio.create_task(self.pipe(client_socket, server_socket, "client"))
            server_to_client = asyncio.create_task(self.pipe(server_socket, client_socket, "server"))

            # Espera até que uma delas termine
            await asyncio.wait(
                [client_to_server, server_to_client],
                return_when=asyncio.FIRST_COMPLETED
            )

        except Exception as e:
            print(f"Proxy error: {e}")
        finally:
            client_socket.close()
            if 'server_socket' in locals():
                server_socket.close()

    async def pipe(self, src_socket: socket.socket, dst_socket: socket.socket, direction: str) -> None:
        try:
            while True:
                data = await asyncio.get_event_loop().sock_recv(src_socket, 4096)
                if not data:
                    break

                # Intercepta o binário
                for facade in self.binary_facades:
                    if direction == "client":
                        await facade.on_client_data_received(data)
                    else:
                        await facade.on_server_data_received(data)

                await asyncio.get_event_loop().sock_sendall(dst_socket, data)

        except Exception as e:
            print(f"Pipe error ({direction}): {e}")
