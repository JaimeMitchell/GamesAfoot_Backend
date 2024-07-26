from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import db
from .location import Location

class Hunt(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_latitude: Mapped[str]
    start_longitude: Mapped[str]
    distance: Mapped[str]
    num_sites: Mapped[str]
    game_type: Mapped[str]
    locations: Mapped[list["Location"]] = relationship(back_populates="hunt")

    def to_dict(self):
        return {
            "id": self.id,
            "start_latitude": self.start_latitude,
            "start_longitude": self.start_longitude,
            "distance": self.distance,
            "num_sites": self.num_sites,
            "game_type": self.game_type
        }

    @classmethod
    def from_dict(cls, data):
        new_hunt = cls(
            start_latitude=data.get("start_latitude"),
            start_longitude=data.get("start_longitude"),
            distance=data.get("distance"),
            num_sites=data.get("num_sites"),
            game_type=data.get("game_type")
        )

        return new_hunt