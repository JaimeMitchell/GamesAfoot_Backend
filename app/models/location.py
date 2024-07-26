from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from ..db import db


class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    latitude: Mapped[str]
    longitude: Mapped[str]
    description: Mapped[str]
    clues: Mapped[list[str]] = mapped_column(ARRAY(String))

    hunt_id: Mapped[int] = mapped_column(ForeignKey("hunt.id"))
    hunt: Mapped["Hunt"] = relationship(back_populates="locations")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "clues": self.clues
        }

    @classmethod
    def from_dict(cls, data):
        new_location = cls(
            name=data.get("name"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            description=data.get("description"),
            clues=data.get("clues")
        )
        return new_location