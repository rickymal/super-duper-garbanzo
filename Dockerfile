# Use uma imagem Go como base
FROM golang:1.21-alpine as builder

# Diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie os arquivos do repositório para o contêiner
COPY . .

# Compila os serviços Go
RUN go mod tidy && go build -o main ./...

# Use uma imagem mais enxuta para a execução do container
FROM alpine:latest

# Instale dependências necessárias
RUN apk --no-cache add ca-certificates

# Copie o binário do build
COPY --from=builder /app/main /usr/local/bin/

# Defina a variável de ambiente
ENV APP_ENV=production

# Exponha a porta do seu serviço (ajuste conforme necessário)
EXPOSE 8080

# Defina o comando de execução
CMD ["main"]
