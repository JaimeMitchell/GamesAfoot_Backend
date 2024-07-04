from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from ..db import db

class Clue(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clue: Mapped[str]
    user_input_id: Mapped[int] = mapped_column(ForeignKey("user_input.id")) 
    user_input: Mapped["UserInput"] = relationship(back_populates="Clue")

def to_dict(self):
        return {
            "id" : self.id,
            "clue" : self.clue,
        }