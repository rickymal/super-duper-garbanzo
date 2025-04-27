
import os

print(os.listdir())
from domain.service.new_server import createServerfactory

server = createServerfactory.new_application(port=8080, host="localhost")
server.add_receiver("/health", "GET", lambda: {"status": "ok"})
server.init()

# agora você já consegue fazer:
#   curl http://localhost:8080/health
#   curl http://localhost:8080/health -X GET
#   curl http://localhost:8080/health -X POST