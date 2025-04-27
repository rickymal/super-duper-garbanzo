from fastapi import FastAPI

###############################################################################
# FastAPI application factory
###############################################################################

def create_app() -> FastAPI:
    """Cria e configura a instância da FastAPI já com rota GraphQL."""


    app = FastAPI(
        title="Mock Gateway Manager API",
        version="0.1.0",
        description="GraphQL endpoint para criar/remover rotas proxy, alternar modos e inspecionar métricas.",
        docs_url="/docs",  # Swagger
        redoc_url="/redoc",
    )

    # ---------------------------------------------------------------------
    # Lifecycles
    # ---------------------------------------------------------------------

    @app.on_event("startup")
    async def _startup() -> None:
        """Inicializa banco e ProxyFactory lazily."""
        pass
    @app.on_event("shutdown")
    async def _shutdown() -> None:
        """Fecha workers e conexões."""
        
        pass

    # ---------------------------------------------------------------------
    # Rotas
    # ---------------------------------------------------------------------

    # GraphQL exposto em /graphql
    app.include_router(graphql_app, prefix="/graphql")

    # Health‑check simples (útil para k8s liveness/readiness probes)
    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok"}
    return app

# Permite executar com:
#   uvicorn app.entrypoints.api:app --reload
app = create_app()

__all__ = ["app", "create_app"]
