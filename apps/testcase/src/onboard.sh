docker run --name meu-postgres \
  -e POSTGRES_DB=meu_banco \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin \
  -p 12432:5432 \
  -d postgres


docker run -d \
  --hostname my-rabbit \
  --name rabbitmq-broker \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
