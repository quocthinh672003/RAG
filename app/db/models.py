# app/db/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, JSON, ForeignKey, DateTime
from datetime import datetime
import uuid

def uuid_str() -> str:
    return uuid.uuid4().hex

class Base(DeclarativeBase):
    pass

class Thread(Base):
    __tablename__ = "threads"
    id: Mapped[str] = mapped_column(String(32), primary_key = True, default = uuid_str)
    title: Mapped[str] = mapped_column(String(255), nullable = False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default = datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default = datetime.utcnow)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable = True)

    messages: Mapped[list["Message"]] = relationship(back_populates="thread", cascade = "all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(32), primary_key = True, default = uuid_str)
    thread_id: Mapped[str] = mapped_column(String(32), ForeignKey("threads.id", ondelete = "cascade"), index = True)
    role: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default = datetime.utcnow)
    model: Mapped[str] = mapped_column(String(255), nullable = True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable = True)

    thread: Mapped["Thread"] = relationship(back_populates="messages")