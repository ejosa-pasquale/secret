from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(str, Enum):
    admin = "admin"
    restaurant = "restaurant"
    customer = "customer"


class AvailabilityStatus(str, Enum):
    available = "available"
    booked = "booked"
    expired = "expired"
    cancelled = "cancelled"


class BookingStatus(str, Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class SubscriptionStatus(str, Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.customer, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    restaurants: Mapped[list["Restaurant"]] = relationship(back_populates="manager")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="customer")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="customer")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    public_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    secret_alias: Mapped[str] = mapped_column(String(160), nullable=False)
    city: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    area: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    cuisine: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    michelin_stars: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    manager: Mapped[User | None] = relationship(back_populates="restaurants")
    availabilities: Mapped[list["Availability"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    reviews: Mapped[list["Review"]] = relationship(back_populates="restaurant")


class Availability(Base):
    __tablename__ = "availabilities"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "service_date", "service_time", name="uq_restaurant_slot"),
        Index("ix_availability_search", "service_date", "city", "cuisine", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    service_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    service_time: Mapped[str] = mapped_column(String(8), nullable=False)
    city: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    cuisine: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_person: Mapped[float] = mapped_column(Float, nullable=False)
    restaurant_fee: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    menu_title: Mapped[str] = mapped_column(String(160), nullable=False)
    menu_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AvailabilityStatus] = mapped_column(SAEnum(AvailabilityStatus), default=AvailabilityStatus.available, index=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="availabilities")
    booking: Mapped["Booking | None"] = relationship(back_populates="availability")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (Index("ix_booking_date_status", "booking_date", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    availability_id: Mapped[int] = mapped_column(ForeignKey("availabilities.id", ondelete="CASCADE"), unique=True, nullable=False)
    booking_code: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), default=BookingStatus.confirmed, index=True, nullable=False)
    booking_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[User] = relationship(back_populates="bookings")
    availability: Mapped[Availability] = relationship(back_populates="booking")
    review: Mapped["Review | None"] = relationship(back_populates="booking")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(80), nullable=False)
    monthly_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.active, index=True, nullable=False)
    starts_at: Mapped[date] = mapped_column(Date, nullable=False)
    expires_at: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped[User] = relationship(back_populates="subscriptions")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("booking_id", name="uq_review_booking"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="review")
    restaurant: Mapped[Restaurant] = relationship(back_populates="reviews")
    customer: Mapped[User] = relationship(back_populates="reviews")
