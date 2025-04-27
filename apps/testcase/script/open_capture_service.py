from library import testsuite, proxyer, handler
import tracemalloc

tracemalloc.start(25)

input_data = {"url": "http://localhost:8080/idempiere-11", "port_proxy": 8080}

from enum import Enum, auto

class Interpol(Enum):
    KNN = auto()

from library import cmd
log_app = []
async def readline(data: str, stream_type: str):
    log_app.append(f"[{stream_type}] {data}")

import rich
console = rich.get_console()

async def open_service(self, url):
    self.process = await cmd.run_script_and_get_pid(["docker", "compose", "up"], './', readline)
    await asyncio.sleep(3)

    console.print(f"return code: {self.process.returncode}")
    if self.process.returncode is None or self.process.returncode == 0:
        self.pg_proxy = proxyer.ProxyServer(
            original_port=5433,
            mirror_port='8080',
            binary_facades=[handler.PostgresFacade],
        )

        await self.pg_proxy.start()
        return
    
    raise cmd.FailTest(
        title="Error starting service",
        log_message="\n".join(log_app)
    )
    
        

    self.pg_proxy.start()


async def close_service(self, url):
    await asyncio.sleep(3)
    self.pg_proxy.stop()
    pass

import asyncio


ts = testsuite.actor("PostgreSQL Application")
ts.step("use {{url}} to get data", open_service)
ts.step("close service at {{url}}", close_service)


asyncio.run(ts.run_all(input_data))