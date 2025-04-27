#!/usr/bin/env python3
"""
goclean.py
~~~~~~~~~~
Gera uma árvore de diretórios/arquivos a partir de um template
definido em código Python usando a classe TemplateBuilder.

Exemplo de uso:

    python goclean.py --design layout.py --dest ./ --dry-run
"""

from __future__ import annotations
import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Union

# ----------- Núcleo do Builder ----------- #

class _DirNode:
    """Nó da árvore (diretório)."""

    def __init__(self, name: str, parent: "_DirNode | None" = None) -> None:
        self.name = name
        self.parent = parent
        self._children: Dict[str, _DirNode] = {}
        self._files: Dict[str, str] = {}  # nome -> conteúdo ("" = vazio)

    # ---- API fluente ---- #

    def new(self, name: str) -> "_DirNode":
        """Cria (ou obtém) um subdiretório."""
        if name not in self._children:
            self._children[name] = _DirNode(name, self)
        return self._children[name]

    def file(self, name: str, content: str = "") -> "_DirNode":
        """Adiciona um arquivo ao diretório atual."""
        self._files[name] = content
        return self

    # ---- Build / materialização ---- #

    def _materialize(self, base: Path, dry: bool) -> None:
        current = base / self.name
        if dry:
            print(f"[DIR]  {current}")
        else:
            current.mkdir(parents=True, exist_ok=True)

        for fname, data in self._files.items():
            fpath = current / fname
            if dry:
                print(f"[FILE] {fpath}")
            else:
                if not fpath.exists():
                    fpath.parent.mkdir(parents=True, exist_ok=True)
                    with fpath.open("w", encoding="utf-8") as fp:
                        fp.write(data)

        for child in self._children.values():
            child._materialize(current, dry)


class TemplateBuilder(_DirNode):
    """Raiz da árvore + metadados."""

    def __init__(self, destination: str | Path, name: str, description: str = "") -> None:
        super().__init__(name)
        self.destination = Path(destination).expanduser().resolve()
        self.description = description

    # entrada de conveniência para compatibilidade com exemplo do usuário
    def new(self, name: str) -> _DirNode:  # type: ignore[override]
        return super().new(name)

    # ---- Execução ---- #

    def build(self, dry_run: bool = False) -> None:
        if dry_run:
            print(f"🏗️  ️[DRY‑RUN] Estrutura '{self.name}' → {self.destination}")
        else:
            print(f"🏗️  Criando estrutura '{self.name}' em {self.destination}")

        self._materialize(self.destination, dry_run)

        if not dry_run:
            print("✅  Concluído.")


# ----------- CLI / Carregamento de template ----------- #

def _import_template(path: Path):
    spec = importlib.util.spec_from_file_location("tmpl", path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"Não foi possível carregar template {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gerador de estrutura (Clean Architecture / DDD)")
    p.add_argument("--design", "-dg", required=True, help="Arquivo .py que define build(tb)")
    p.add_argument("--dest", "-dst", default=".", help="Diretório destino da estrutura")
    p.add_argument("--name", "-n", default="project-root", help="Nome da pasta‑raiz criada")
    p.add_argument("--desc", default="", help="Descrição (opcional)")
    p.add_argument("--dry-run", action="store_true", help="Somente exibir, não criar")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    tmpl_path = Path(args.template).expanduser()

    if not tmpl_path.is_file():
        sys.exit(f"❌  Template não encontrado: {tmpl_path}")

    module = _import_template(tmpl_path)
    if not hasattr(module, "build"):
        sys.exit("❌  O template precisa definir uma função  build(tb)")

    tb = TemplateBuilder(destination=args.dest, name=args.name, description=args.desc)
    # Executa a função do usuário para popular a árvore
    module.build(tb)

    tb.build(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
