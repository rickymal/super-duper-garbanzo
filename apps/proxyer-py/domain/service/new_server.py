# service/server_factory.py
import threading
import uvicorn
from fastapi import FastAPI

class AppWrapper:
    """Objetinho que devolvemos ao chamador
    para poder adicionar rotas e ligar o servidor."""
    def __init__(self, app: FastAPI, server: uvicorn.Server):
        self._app = app
        self._server = server
        self._thread: threading.Thread | None = None

    # ---- API pública ----
    def add_receiver(self, path: str, method: str, func):
        self._app.add_api_route(path, func, methods=[method])

    def init(self):
        # executa o servidor em thread daemon
        self._thread = threading.Thread(
            target=self._server.run, daemon=True
        )
        self._thread.start()

    # opcional: desligar
    def shutdown(self):
        if self._server.started:
            self._server.should_exit = True
            self._thread.join(timeout=5)


class ServerFactory:
    """Fábrica de mini‑servidores FastAPI+Uvicorn em runtime."""
    def __init__(self):
        self._apps: list[AppWrapper] = []

    def new_application(self, *, port: int, host: str = "127.0.0.1") -> AppWrapper:
        app = FastAPI()
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            loop="asyncio",
            log_level="info",
            lifespan="on",
        )
        server = uvicorn.Server(config)
        wrapper = AppWrapper(app, server)
        self._apps.append(wrapper)
        return wrapper

# ----------------- uso -----------------

createServerfactory = ServerFactory()
