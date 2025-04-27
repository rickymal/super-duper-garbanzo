# hello.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.post("/")
def hello():
    _ = request.get_json(silent=True)   # lê/descarta o JSON recebido
    return jsonify(msg="Olá mundo")     # responde sempre igual

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
