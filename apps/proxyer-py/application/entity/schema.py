from __future__ import annotations

"""GraphQL Schema (Strawberry) – expõe rotas e operações de gerenciamento.

Este módulo fica em `app/infra/graphql/schema.py` e é importado pelo `api.py`.
Ele faz ponte entre a camada GraphQL e os *UseCases* da aplicação.
"""

import asyncio
from datetime import datetime
from typing import List, Optional

import strawberry
from strawberry.types import Info

# ---------------------------------------------------------------------------
# Domain DTOs (expostos na API)
# ---------------------------------------------------------------------------

@strawberry.type
class Route:
    id: int
    listen_port: int
    target_host: str
    target_port: int
    protocol: str
    mode: str  # "proxy" | "mock"
    created_at: datetime


# ---------------------------------------------------------------------------
# Input Objects
# ---------------------------------------------------------------------------

@strawberry.input
class CreateRouteInput:
    listen_port: int
    target_host: str
    target_port: int
    protocol: str = "tcp"  # default
    mode: str = "proxy"     # default


@strawberry.input
class FaultConfigInput:
    timeout_ms: Optional[int] = 0
    reset_probability: Optional[float] = 0.0
    byte_flip: Optional[bool] = False


# ---------------------------------------------------------------------------
# Dependency helpers (simplificados)
# ---------------------------------------------------------------------------

def get_usecases(info: Info):
    """Helper para extrair container ou di do contexto.
    No create_app() passamos `context_value={"container": container}` (não mostrado aqui).
    """
    return info.context["container"]


# ---------------------------------------------------------------------------
# Query Root
# ---------------------------------------------------------------------------

@strawberry.type
class Query:
    @strawberry.field
    async def routes(self, info: Info) -> List[Route]:
        usecases = get_usecases(info)
        list_routes_uc = usecases["list_routes"]  # UseCase injetado
        return await list_routes_uc.execute()

    @strawberry.field
    async def route(self, info: Info, route_id: int) -> Optional[Route]:
        usecases = get_usecases(info)
        get_uc = usecases["get_route"]
        return await get_uc.execute(route_id)


# ---------------------------------------------------------------------------
# Mutation Root
# ---------------------------------------------------------------------------

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_route(self, info: Info, data: CreateRouteInput) -> Route:
        usecases = get_usecases(info)
        create_uc = usecases["create_route"]
        cmd = {
            "listen_port": data.listen_port,
            "target_host": data.target_host,
            "target_port": data.target_port,
            "protocol": data.protocol,
            "mode": data.mode,
        }
        return await create_uc.execute(cmd)

    @strawberry.mutation
    async def remove_route(self, info: Info, route_id: int) -> bool:
        usecases = get_usecases(info)
        remove_uc = usecases["remove_route"]
        return await remove_uc.execute(route_id)

    @strawberry.mutation
    async def switch_mode(self, info: Info, route_id: int, mode: str) -> Route:
        usecases = get_usecases(info)
        switch_uc = usecases["switch_mode"]
        return await switch_uc.execute(route_id, mode)

    @strawberry.mutation
    async def update_faults(self, info: Info, route_id: int, faults: FaultConfigInput) -> Route:
        usecases = get_usecases(info)
        update_faults_uc = usecases["update_faults"]
        faults_dict = {
            "timeout_ms": faults.timeout_ms,
            "reset_probability": faults.reset_probability,
            "byte_flip": faults.byte_flip,
        }
        return await update_faults_uc.execute(route_id, faults_dict)


# ---------------------------------------------------------------------------
# Compose schema
# ---------------------------------------------------------------------------

schema = strawberry.Schema(Query, Mutation)
