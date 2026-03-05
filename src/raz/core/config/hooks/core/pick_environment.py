from __future__ import annotations

from raz.core.hooks.base import Hook


class PickEnvironment(Hook):
    def execute(self, context, **kwargs) -> str:
        """Pick the environment to use for the current execution.

        context: Context
        returns: environment name string
        """
        entity = getattr(context, "entity", None)
        step = getattr(context, "step", None)

        if entity == "project":
            return "project"

        if entity == "shot":
            return "shot_step" if step else "shot"

        if entity == "asset":
            return "asset_step" if step else "asset"

        # safe fallback
        return "project"
