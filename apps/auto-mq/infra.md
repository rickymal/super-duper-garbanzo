# Infraestrutura do Projeto

Este documento descreve a estrutura de diretórios do projeto:

- **cmd/app**: Arquivo principal da aplicação (main.go).
- **internal/domain**: Contém modelos e regras de negócio (entidades e objetos de valor).
- **internal/application**: Lógica dos casos de uso e serviços que orquestram as regras de negócio.
- **internal/infrastructure**: Implementações técnicas e integrações com sistemas externos.
- **internal/patterns**: Exemplos e organização dos design patterns utilizados.
  - **creational**: Padrões de criação (Factory, Builder, Abstract Factory, Prototype).
  - **structural**: Padrões estruturais (Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy).
  - **behavioral**: Padrões comportamentais (Chain of Responsibility, Command, Iterator, Mediator, Observer, State, Strategy, Template Method, Visitor).
- **pkg/utils**: Pacotes utilitários, como o logger.
- **go.mod / go.sum**: Gerenciamento de dependências do Go.

Essa organização tem como objetivo facilitar o entendimento e a manutenção do código,
alinhando as soluções de design aos requisitos e à complexidade do domínio.
