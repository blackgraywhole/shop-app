from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from sqlalchemy import ForeignKey, Text
from datetime import datetime


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    comment: Mapped[str] = mapped_column(nullable=True)
    comment_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    grade: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
