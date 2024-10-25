FROM python:3.12-slim

# Crie um usuário não privilegiado
RUN useradd -m appuser

# Defina o diretório de trabalho e mude o proprietário
WORKDIR /home/appuser/app
COPY --chown=appuser:appuser . /home/appuser/app

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Mude para o usuário não privilegiado
USER appuser

# Defina o comando de entrada
CMD ["sleep", "infinity"]
# CMD ["tail", "-f", "/dev/null"]