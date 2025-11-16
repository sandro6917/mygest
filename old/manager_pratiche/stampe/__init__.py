from __future__ import annotations

class LabelRegistry:
    def __init__(self):
        self._layouts = {}  # key: "app_label.model" -> callable(instance, canvas, width, height)

    def register(self, app_label: str, model: str, layout_callable):
        key = f"{app_label}.{model}".lower()
        self._layouts[key] = layout_callable

    def get(self, app_label: str, model: str):
        return self._layouts.get(f"{app_label}.{model}".lower())

registry = LabelRegistry()