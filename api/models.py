from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Text, UniqueConstraint, Table, DateTime, func
from sqlalchemy.orm import relationship

from database import Base

judge_categories = Table(
    "judge_categories", Base.metadata,
    Column("judge_id", Integer, ForeignKey("judges.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    breeds = relationship("Breed", back_populates="category")
    judges = relationship("Judge", secondary=judge_categories, back_populates="categories")
    rings = relationship("RingCategory", back_populates="category")


class Breed(Base):
    __tablename__ = "breeds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    breed_code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    category = relationship("Category", back_populates="breeds")
    cats = relationship("Cat", back_populates="breed_rel")


class Judge(Base):
    __tablename__ = "judges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    photo = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    flag = Column(String(2), nullable=True)

    categories = relationship("Category", secondary=judge_categories, back_populates="judges")
    rings = relationship("Ring", back_populates="judge_rel")
    shows = relationship("Show", secondary="judge_shows", back_populates="judges")


judge_shows = Table(
    "judge_shows", Base.metadata,
    Column("judge_id", Integer, ForeignKey("judges.id", ondelete="CASCADE"), primary_key=True),
    Column("show_id", Integer, ForeignKey("shows.id", ondelete="CASCADE"), primary_key=True),
)


class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    start_date = Column(String(10), nullable=True)
    end_date = Column(String(10), nullable=True)
    status = Column(String(50), default="draft")

    days = relationship("ShowDay", back_populates="show", cascade="all, delete-orphan",
                        order_by="ShowDay.sort_order")
    judges = relationship("Judge", secondary="judge_shows", back_populates="shows")


class ShowDay(Base):
    __tablename__ = "show_days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    show_id = Column(Integer, ForeignKey("shows.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False)

    show = relationship("Show", back_populates="days")
    rings = relationship("Ring", back_populates="day", cascade="all, delete-orphan",
                         order_by="Ring.ring_number")
    cat_entries = relationship("CatShowDay", back_populates="day", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("show_id", "sort_order"),
    )


class Ring(Base):
    __tablename__ = "rings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    show_day_id = Column(Integer, ForeignKey("show_days.id", ondelete="CASCADE"), nullable=False)
    ring_number = Column(Integer, nullable=False)
    judge_id = Column(Integer, ForeignKey("judges.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="active")
    current_catalog_nr = Column(Integer, nullable=True)
    current_class = Column(String(50), nullable=True)
    pause_message = Column(String(500), nullable=True)

    day = relationship("ShowDay", back_populates="rings")
    judge_rel = relationship("Judge", back_populates="rings")
    categories = relationship("RingCategory", back_populates="ring", cascade="all, delete-orphan")
    queue_entries = relationship("RingQueue", back_populates="ring", cascade="all, delete-orphan",
                                 order_by="RingQueue.sequence_order")

    __table_args__ = (
        UniqueConstraint("show_day_id", "ring_number"),
    )


class RingCategory(Base):
    __tablename__ = "ring_categories"

    ring_id = Column(Integer, ForeignKey("rings.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)

    ring = relationship("Ring", back_populates="categories")
    category = relationship("Category", back_populates="rings")


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    cats = relationship("Cat", back_populates="owner_rel")


class Cat(Base):
    __tablename__ = "cats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    breed_ems = Column(String(10), ForeignKey("breeds.breed_code", ondelete="RESTRICT"), nullable=False)
    gender = Column(String(1), nullable=False)
    show_class = Column(String(50), nullable=False)
    birth_date = Column(String(10), nullable=True)
    registration_nr = Column(String(50), nullable=True)
    owner_id = Column(Integer, ForeignKey("owners.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="present")

    breed_rel = relationship("Breed", back_populates="cats")
    owner_rel = relationship("Owner", back_populates="cats")
    days = relationship("CatShowDay", back_populates="cat", cascade="all, delete-orphan")
    queue_entries = relationship("RingQueue", back_populates="cat", cascade="all, delete-orphan")


class CatShowDay(Base):
    __tablename__ = "cat_show_days"

    cat_id = Column(Integer, ForeignKey("cats.id", ondelete="CASCADE"), primary_key=True)
    show_day_id = Column(Integer, ForeignKey("show_days.id", ondelete="CASCADE"), primary_key=True)
    catalog_nr = Column(Integer, nullable=False)
    status = Column(String(50), default="unchecked")

    cat = relationship("Cat", back_populates="days")
    day = relationship("ShowDay", back_populates="cat_entries")

    __table_args__ = (
        UniqueConstraint("show_day_id", "catalog_nr"),
    )


class RingQueue(Base):
    __tablename__ = "ring_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ring_id = Column(Integer, ForeignKey("rings.id", ondelete="CASCADE"), nullable=False)
    cat_id = Column(Integer, ForeignKey("cats.id", ondelete="CASCADE"), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")

    ring = relationship("Ring", back_populates="queue_entries")
    cat = relationship("Cat", back_populates="queue_entries")

    __table_args__ = (
        UniqueConstraint("ring_id", "sequence_order"),
    )


class DisplayDevice(Base):
    __tablename__ = "display_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False, default="Unnamed Display")
    device_type = Column(String(50), nullable=False, default="day_display")
    show_id = Column(Integer, nullable=True)
    day_id = Column(Integer, nullable=True)
    last_connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
