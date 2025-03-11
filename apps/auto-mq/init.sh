#!/bin/bash
# Script para criar a estrutura de projeto baseada em design patterns,
# com templates de código para cada arquivo Go e com readme.md e infra.md.
#
# Uso:
#   ./cria_estrutura.sh --folder nome_da_pasta
#   ou
#   ./cria_estrutura.sh --folder .
#
# Se o parâmetro --folder não for informado, será usado "project" como padrão.

# Verifica se o parâmetro --folder foi passado e possui um valor
if [ "$1" == "--folder" ] && [ -n "$2" ]; then
    base_folder="$2"
else
    base_folder="."
fi

echo "Criando estrutura de projeto na pasta: $base_folder"

# Se base_folder não for o diretório atual, cria a pasta base (caso não exista)
if [ "$base_folder" != "." ]; then
    mkdir -p "$base_folder"
fi

# Criação dos diretórios principais
mkdir -p "$base_folder/cmd/app"
mkdir -p "$base_folder/internal/domain"
mkdir -p "$base_folder/internal/application"
mkdir -p "$base_folder/internal/infrastructure"

# Diretórios para os padrões de criação (Creational)
mkdir -p "$base_folder/internal/patterns/creational/factory"
mkdir -p "$base_folder/internal/patterns/creational/builder"
mkdir -p "$base_folder/internal/patterns/creational/abstract_factory"
mkdir -p "$base_folder/internal/patterns/creational/prototype"

# Diretórios para os padrões estruturais (Structural)
mkdir -p "$base_folder/internal/patterns/structural/adapter"
mkdir -p "$base_folder/internal/patterns/structural/bridge"
mkdir -p "$base_folder/internal/patterns/structural/composite"
mkdir -p "$base_folder/internal/patterns/structural/decorator"
mkdir -p "$base_folder/internal/patterns/structural/facade"
mkdir -p "$base_folder/internal/patterns/structural/flyweight"
mkdir -p "$base_folder/internal/patterns/structural/proxy"

# Diretórios para os padrões comportamentais (Behavioral)
mkdir -p "$base_folder/internal/patterns/behavioral/chain_of_responsibility"
mkdir -p "$base_folder/internal/patterns/behavioral/command"
mkdir -p "$base_folder/internal/patterns/behavioral/iterator"
mkdir -p "$base_folder/internal/patterns/behavioral/mediator"
mkdir -p "$base_folder/internal/patterns/behavioral/observer"
mkdir -p "$base_folder/internal/patterns/behavioral/state"
mkdir -p "$base_folder/internal/patterns/behavioral/strategy"
mkdir -p "$base_folder/internal/patterns/behavioral/template"
mkdir -p "$base_folder/internal/patterns/behavioral/visitor"

# Diretórios utilitários
mkdir -p "$base_folder/pkg/utils"

#######################################
# Criação dos arquivos com templates  #
#######################################

# cmd/app/main.go: Hello World
cat <<EOF > "$base_folder/cmd/app/main.go"
package main

import "fmt"

func main() {
    fmt.Println("Hello, world!")
}
EOF

# Creational patterns
cat <<EOF > "$base_folder/internal/patterns/creational/factory/factory.go"
package factory

// Factory pattern template
// To implement: Implement Factory pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/creational/builder/builder.go"
package builder

// Builder pattern template
// To implement: Implement Builder pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/creational/abstract_factory/abstract_factory.go"
package abstract_factory

// Abstract Factory pattern template
// To implement: Implement Abstract Factory pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/creational/prototype/prototype.go"
package prototype

// Prototype pattern template
// To implement: Implement Prototype pattern
EOF

# Structural patterns
cat <<EOF > "$base_folder/internal/patterns/structural/adapter/adapter.go"
package adapter

// Adapter pattern template
// To implement: Implement Adapter pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/structural/bridge/bridge.go"
package bridge

// Bridge pattern template
// To implement: Implement Bridge pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/structural/composite/composite.go"
package composite

// Composite pattern template
// To implement: Implement Composite pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/structural/decorator/decorator.go"
package decorator

// Decorator pattern template
// To implement: Implement Decorator pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/structural/facade/facade.go"
package facade

// Facade pattern template
// To implement: Implement Facade pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/structural/flyweight/flyweight.go"
package flyweight

// Flyweight pattern template
// To implement: Implement Flyweight pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/structural/proxy/proxy.go"
package proxy

// Proxy pattern template
// To implement: Implement Proxy pattern
EOF

# Behavioral patterns
cat <<EOF > "$base_folder/internal/patterns/behavioral/chain_of_responsibility/chain_of_responsibility.go"
package chain_of_responsibility

// Chain of Responsibility pattern template
// To implement: Implement Chain of Responsibility pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/command/command.go"
package command

// Command pattern template
// To implement: Implement Command pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/iterator/iterator.go"
package iterator

// Iterator pattern template
// To implement: Implement Iterator pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/mediator/mediator.go"
package mediator

// Mediator pattern template
// To implement: Implement Mediator pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/observer/observer.go"
package observer

// Observer pattern template
// To implement: Implement Observer pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/state/state.go"
package state

// State pattern template
// To implement: Implement State pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/strategy/strategy.go"
package strategy

// Strategy pattern template
// To implement: Implement Strategy pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/template/template.go"
package template

// Template Method pattern template
// To implement: Implement Template Method pattern
EOF

cat <<EOF > "$base_folder/internal/patterns/behavioral/visitor/visitor.go"
package visitor

// Visitor pattern template
// To implement: Implement Visitor pattern
EOF

# Utilitário: pkg/utils/logger.go
cat <<EOF > "$base_folder/pkg/utils/logger.go"
package utils

import "log"

// Logger is a simple logging utility
func Logger(message string) {
    log.Println(message)
}
EOF

# Arquivos de gerenciamento de dependências do Go
cat <<EOF > "$base_folder/go.mod"
module your_module_name

go 1.22.2
EOF

cat <<EOF > "$base_folder/go.sum"
# go.sum file placeholder
EOF

#######################################
# Criação dos arquivos de documentação #
#######################################

# readme.md com visão geral do projeto
cat <<EOF > "$base_folder/readme.md"
# Projeto Pattern-Driven Design

Este projeto foi gerado utilizando um script shell que organiza a estrutura de diretórios e arquivos
baseado em design patterns e nos princípios do Domain-Driven Design (DDD).

## Estrutura Geral

- **cmd/**: Contém o ponto de entrada da aplicação.
- **internal/**: Separa o domínio, aplicação, infraestrutura e os exemplos de design patterns.
- **pkg/**: Pacotes utilitários compartilhados.
- **go.mod / go.sum**: Arquivos de gerenciamento de dependências do Go.

Para mais detalhes sobre a estrutura interna, veja o arquivo [infra.md](./infra.md).
EOF

# infra.md com descrição da infraestrutura
cat <<EOF > "$base_folder/infra.md"
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
EOF

echo "Estrutura de projeto criada com sucesso na pasta: $base_folder"
