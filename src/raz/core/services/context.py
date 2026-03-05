from __future__ import annotations

from dataclasses import replace

from raz.core.context.model import ContextSnapshot
from raz.core.services.errors import ContextError


class ContextService:
    """
    Thin orchestration around ContextManager.
    Keeps CoreEngine API simple and avoids apps touching internals.
    """

    def __init__(self, context_manager):
        self._ctx = context_manager

    def get(self) -> ContextSnapshot:
        return self._ctx.get()

    def set(
        self,
        *,
        project: str | None = None,
        entity_type: str | None = None,
        entity: str | None = None,
        task: str | None = None,
        asset: str | None = None,
        user: str | None = None,
        meta: dict | None = None,
    ) -> ContextSnapshot:
        current = self._ctx.get()
        updated = replace(
            current,
            project=project or current.project,
            entity_type=entity_type or current.entity_type,
            entity=entity or current.entity,
            asset=asset if asset is not None else current.asset,
            user=user if user is not None else current.user,
            meta=meta if meta is not None else current.meta,
        )
        try:
            self._ctx.set(updated)
        except Exception as e:
            raise ContextError(str(e)) from e
        return updated