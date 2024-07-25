from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import db
from .location import Location

class UserInput(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    latitude: Mapped[str]
    longitude: Mapped[str]
    distance: Mapped[str]
    num_sites: Mapped[str]
    game_type: Mapped[str]
    locations: Mapped[list["Location"]] = relationship(back_populates="user_input")

    def to_dict(self):
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance": self.distance,
            "num_sites": self.num_sites,
            "game_type": self.game_type
        }

    @classmethod
    def from_dict(cls, data):
        new_user_input = cls(
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            distance=data.get("distance"),
            num_sites=data.get("num_sites"),
            game_type=data.get("game_type")
        )

        return new_user_input