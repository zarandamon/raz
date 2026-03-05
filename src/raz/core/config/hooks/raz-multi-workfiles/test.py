from __future__ import annotations

from raz.core.hooks.base import Hook

class TestHook(Hook):
    def execute(self, context, **kwargs) -> str:
        """
        A simple test hook for demonstration purposes.
        """
        context_entity = getattr(context, "entity", None)
        context_step = getattr(context, "step", None)
        return f"TestHook executed with context: {context_entity}, {context_step}"