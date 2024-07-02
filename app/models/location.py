from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from ..db import db

class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]
    description: Mapped[str]
    clue: Mapped[str]

    user_input_id: Mapped[int] = mapped_column(ForeignKey("user_input.id"))
    user_input: Mapped["UserInput"] = relationship(back_populates="locations")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "clue": self.clue
        }

    @classmethod
    def from_dict(cls, data):
        new_location = cls(
            name=data.get("name"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            description=data.get("description"),
            clue=data.get("clue")
        )
        return new_location