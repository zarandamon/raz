from __future__ import annotations

from typing import Any, Dict, List, Protocol

from raz.core.context.model import Context


class RegistryPort(Protocol):
    """Version authority + records."""

    def reserve_next_version(self, context: Context) -> int: ...
    def register_workfile(
        self,
        context: Context,
        path: str,
        version: int,
        meta: Dict[str, Any] | None = None,
    ) -> None: ...

    def list_records(self, context: Context, kind: str = "workfile") -> List[Dict[str, Any]]: ...