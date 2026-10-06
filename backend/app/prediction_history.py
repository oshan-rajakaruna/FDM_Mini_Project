"""MongoDB persistence for successful RainWise predictions."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError


COLLECTION_NAME = "predictions"
CREATED_AT_INDEX_NAME = "createdAt_desc"


class PredictionHistoryError(RuntimeError):
    """Base class for safe prediction-history storage errors."""


class PredictionPersistenceError(PredictionHistoryError):
    """Raised when a successful prediction cannot be persisted."""


class PredictionHistoryRepository:
    """Store compact prediction history records in MongoDB."""

    __slots__ = ("_collection",)

    def __init__(self, database: Database) -> None:
        self._collection = database.get_collection(COLLECTION_NAME)

    def ensure_indexes(self) -> None:
        """Create the index used by future newest-first history queries."""

        try:
            self._collection.create_index(
                [("createdAt", DESCENDING)],
                name=CREATED_AT_INDEX_NAME,
            )
        except PyMongoError:
            raise PredictionHistoryError(
                "Unable to prepare prediction history storage."
            ) from None

    def save_prediction(
        self,
        *,
        observation_date: date,
        location: str,
        prediction: str,
        rain_probability: float,
    ) -> Any:
        """Persist one successful model result and return its MongoDB id."""

        document = {
            "observationDate": observation_date.isoformat(),
            "location": location,
            "prediction": prediction,
            "rainProbability": rain_probability,
            "createdAt": datetime.now(timezone.utc),
        }

        try:
            result = self._collection.insert_one(document)
        except PyMongoError:
            raise PredictionPersistenceError(
                "The prediction could not be saved."
            ) from None

        if not result.acknowledged:
            raise PredictionPersistenceError(
                "The prediction save was not acknowledged."
            )
        return result.inserted_id
