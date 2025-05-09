import asyncio

import socket
import psutil  # você pode instalar via: pip install psutil

def is_port_in_use(port: int, host="localhost") -> bool:
    """
    Verifica se uma porta já está em uso.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout):
            return False
        except Exception:
            return True  # Em dúvida, melhor considerar que está em uso.

def kill_process_on_port(port: int):
    """
    Mata qualquer processo usando a porta.
    """
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            if conn.pid:
                p = psutil.Process(conn.pid)
                print(f"Matando processo PID {conn.pid} que usa a porta {port}...")
                p.kill()

def ensure_port_is_free(port: int, host="localhost"):
    """
    Garante que a porta esteja livre antes de seguir.
    """
    if is_port_in_use(port, host):
        print(f"Atenção: porta {port} está ocupada! Tentando liberar...")
        kill_process_on_port(port)
    else:
        print(f"Porta {port} está livre!")


class ProxyServer:
    def __init__(self, original_port, mirror_host, mirror_port, binary_facades=None, original_host="localhost"):
        self.original_port = original_port
        self.mirror_host = mirror_host
        self.mirror_port = mirror_port
        self.binary_facades = binary_facades or []
        self.host = host
        self.event_loop = asyncio.get_running_loop()

    async def stop(self):
        self.server_socket.close()

    async def start(self):
        ensure_port_is_free(self.original_port, self.original_host)
        server = await asyncio.start_server(
            self.handle_client,
            host=self.original_host,
            port=self.original_port
        )

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        try:
            # Conectando ao servidor destino
            server_reader, server_writer = await asyncio.open_connection(
                self.mirror_host,
                self.mirror_port
            )

            # Cria pipes bidirecionais
            client_to_server = asyncio.create_task(self.pipe(client_reader, server_writer, "client"))
            server_to_client = asyncio.create_task(self.pipe(server_reader, client_writer, "server"))

            # Espera terminar uma direção (por exemplo, conexão fechada)
            await asyncio.wait(
                [client_to_server, server_to_client],
                return_when=asyncio.FIRST_COMPLETED
            )

        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            client_writer.close()
            try:
                await client_writer.wait_closed()
            except Exception:
                pass
            if 'server_writer' in locals():
                server_writer.close()
                try:
                    await server_writer.wait_closed()
                except Exception:
                    pass

    async def pipe(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, direction: str):
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break

                # Intercepta o binário
                for facade in self.binary_facades:
                    if direction == "client":
                        await facade.on_client_data_received(data)
                    else:
                        await facade.on_server_data_received(data)

                writer.write(data)
                await writer.drain()
        except Exception as e:
            print(f"Pipe error ({direction}): {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
