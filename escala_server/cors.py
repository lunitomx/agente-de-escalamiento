"""CORS middleware for Escala server."""


class CORSHandler:
    """Adds CORS headers to HTTP responses."""

    @staticmethod
    def get_headers() -> dict[str, str]:
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400",
        }
