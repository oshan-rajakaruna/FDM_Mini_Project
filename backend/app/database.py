"""Process-level MongoDB connection management for RainWise."""

from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from .config import Settings, settings


class MongoServiceError(RuntimeError):
    """Base class for safe MongoDB startup and connectivity errors."""


class MongoConfigurationError(MongoServiceError):
    """Raised when required MongoDB configuration is unavailable."""


class MongoConnectionError(MongoServiceError):
    """Raised when the configured MongoDB deployment cannot be reached."""


class MongoService:
    """Own one MongoClient and its configured database for this process."""

    __slots__ = ("_client", "_database", "_settings")

    def __init__(self, runtime_settings: Settings) -> None:
        self._settings = runtime_settings
        self._client: MongoClient | None = None
        self._database: Database | None = None

    @property
    def database(self) -> Database:
        """Return the connected database for future repository services."""

        if self._database is None:
            raise MongoConnectionError("MongoDB is not connected.")
        return self._database

    @property
    def is_ready(self) -> bool:
        """Return whether this service currently owns a connected client."""

        return self._client is not None and self._database is not None

    def connect(self) -> None:
        """Create and verify the process client without exposing credentials."""

        uri = self._settings.mongodb_uri
        if uri is None:
            raise MongoConfigurationError(
                "MongoDB configuration is missing MONGODB_URI."
            )

        if self.is_ready:
            if self.ping():
                return
            self.close()

        client: MongoClient | None = None
        try:
            client = MongoClient(
                uri,
                appname="RainWise API",
                connectTimeoutMS=5_000,
                serverSelectionTimeoutMS=5_000,
                tz_aware=True,
            )
            client.admin.command("ping")
            database = client.get_database(self._settings.mongodb_database)
        except (PyMongoError, ValueError, TypeError):
            if client is not None:
                client.close()
            raise MongoConnectionError(
                "Unable to connect to the configured MongoDB database."
            ) from None

        self._client = client
        self._database = database

    def ping(self) -> bool:
        """Check current database connectivity without leaking driver errors."""

        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
        except PyMongoError:
            return False
        return True

    def close(self) -> None:
        """Close the client and release process connection resources."""

        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None


@lru_cache(maxsize=1)
def get_mongo_service() -> MongoService:
    """Return the reusable MongoDB service for this API process."""

    return MongoService(settings)
