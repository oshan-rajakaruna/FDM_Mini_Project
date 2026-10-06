"""MongoDB persistence for successful RainWise predictions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError


COLLECTION_NAME = "predictions"
CREATED_AT_INDEX_NAME = "createdAt_desc"


class PredictionHistoryError(RuntimeError):
    """Base class for safe prediction-history storage errors."""


class PredictionPersistenceError(PredictionHistoryError):
    """Raised when a successful prediction cannot be persisted."""


class PredictionHistoryReadError(PredictionHistoryError):
    """Raised when prediction history cannot be read."""


class PredictionHistoryDeleteError(PredictionHistoryError):
    """Raised when prediction history cannot be deleted."""


class InvalidPredictionHistoryId(PredictionHistoryError):
    """Raised when a supplied history id is not a MongoDB ObjectId."""


class PredictionHistoryNotFound(PredictionHistoryError):
    """Raised when no prediction matches a valid history id."""


@dataclass(frozen=True, slots=True)
class PredictionHistoryRecord:
    """Public history data read from a stored prediction document."""

    id: str
    observation_date: str
    location: str
    prediction: str
    rain_probability: float
    created_at: datetime


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

    def list_predictions(self) -> list[PredictionHistoryRecord]:
        """Return saved predictions newest-first with public fields only."""

        try:
            documents = self._collection.find(
                {},
                {
                    "observationDate": 1,
                    "location": 1,
                    "prediction": 1,
                    "rainProbability": 1,
                    "createdAt": 1,
                },
            ).sort("createdAt", DESCENDING)
            return [
                PredictionHistoryRecord(
                    id=str(document["_id"]),
                    observation_date=document["observationDate"],
                    location=document["location"],
                    prediction=document["prediction"],
                    rain_probability=float(document["rainProbability"]),
                    created_at=document["createdAt"],
                )
                for document in documents
            ]
        except (PyMongoError, KeyError, TypeError, ValueError):
            raise PredictionHistoryReadError(
                "Prediction history could not be loaded."
            ) from None

    def delete_prediction(self, record_id: str) -> None:
        """Delete exactly one prediction selected by its MongoDB id."""

        try:
            object_id = ObjectId(record_id)
        except (InvalidId, TypeError):
            raise InvalidPredictionHistoryId(
                "The prediction history id is invalid."
            ) from None

        try:
            result = self._collection.delete_one({"_id": object_id})
        except PyMongoError:
            raise PredictionHistoryDeleteError(
                "The prediction history record could not be deleted."
            ) from None

        if result.deleted_count == 0:
            raise PredictionHistoryNotFound(
                "The prediction history record was not found."
            )

    def delete_all_predictions(self) -> int:
        """Delete all history documents without dropping the collection."""

        try:
            result = self._collection.delete_many({})
        except PyMongoError:
            raise PredictionHistoryDeleteError(
                "Prediction history could not be cleared."
            ) from None
        return result.deleted_count
