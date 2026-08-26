"""API Router — lightweight URL dispatch for the Escala server."""

import re
from collections.abc import Callable


class Router:
    """Simple path-based router for HTTP methods.

    Supports path parameters via {param} syntax:
        /api/worksheets/{category}/{tool}

    Dispatch returns the handler function with matched params bound.
    """

    def __init__(self):
        self._routes: list[tuple[str, re.Pattern, Callable, list[str]]] = []

    def get(self, path: str):
        """Decorator: register a GET route."""
        return self._route("GET", path)

    def post(self, path: str):
        """Decorator: register a POST route."""
        return self._route("POST", path)

    def patch(self, path: str):
        """Decorator: register a PATCH route."""
        return self._route("PATCH", path)

    def delete(self, path: str):
        """Decorator: register a DELETE route."""
        return self._route("DELETE", path)

    def _route(self, method: str, path: str):
        # Extract parameter names and build regex
        param_names = re.findall(r"\{(\w+)\}", path)
        regex_str = "^" + re.sub(r"\{\w+\}", r"([^/]+)", path) + "$"
        pattern = re.compile(regex_str)

        def decorator(handler: Callable):
            self._routes.append((method, pattern, handler, param_names))
            return handler

        return decorator

    def dispatch(
        self, method: str, path: str
    ) -> tuple[Callable | None, dict[str, str]]:
        """Find handler for method+path. Returns (handler, path_params) or (None, {})."""
        for route_method, pattern, handler, param_names in self._routes:
            if route_method != method:
                continue
            match = pattern.match(path)
            if match:
                params = dict(zip(param_names, match.groups()))
                return handler, params
        return None, {}
