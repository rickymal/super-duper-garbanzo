#!/bin/bash
# Exemplo de script que cria um processo em segundo plano e exibe o PID

# Cria um processo fictício (por exemplo, um sleep de 100 segundos)
nohup sleep 10 > /dev/null 2>&1 &

# Obtém o PID do último processo iniciado em background e exibe no padrão PID:<numero>
echo "PID:$!"
