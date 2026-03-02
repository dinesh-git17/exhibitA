"""Executable module entrypoint: python -m app."""

import uvicorn

from app.config import Settings


def main() -> None:
    """Start the Exhibit A backend server."""
    settings = Settings()
    uvicorn.run(
        "app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
