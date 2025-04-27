from goclean import TemplateBuilder  # só para hints; import não é obrigatório

def build(tb: TemplateBuilder):
    """
    Constrói a estrutura usando a DSL fluente `new()` e `file()`.
    """
    # ---------- topo ----------
    tb.file(".gitignore").file("README.md", "# Meu Projeto\n")

    # ---------- cmd ----------
    cmd = tb.new("cmd").new("service")
    cmd.file("main.go", "package main\n\nfunc main() {}\n")

    # ---------- configs ----------
    tb.new("configs").file("default.yaml").file("production.yaml")

    # ---------- internal ----------
    internal = tb.new("internal")

    domain = internal.new("domain")
    for sub in ("entity", "enum", "repository", "service", "event"):
        domain.new(sub)

    application = internal.new("application")
    for sub in ("usecase", "command", "query", "dto"):
        application.new(sub)

    iface = internal.new("interfaces")
    iface.new("http").new("controllers").new("middlewares")
    iface.new("grpc")
    iface.new("cli")

    infra = internal.new("infrastructure")
    persist = infra.new("persistence")
    for db in ("postgres", "mongodb", "mysql"):
        persist.new(db)
    messaging = infra.new("messaging")
    messaging.new("rabbitmq").new("kafka")
    infra.new("external").new("httpclient")
    infra.new("cache").new("redis")

    shared = internal.new("shared")
    for sub in ("errors", "utils", "logging", "constants"):
        shared.new(sub)

    # ---------- raiz extra ----------
    for extra in ("pkg", "scripts", "tests", "docs", "tools"):
        tb.new(extra)