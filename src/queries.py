from __future__ import annotations

from datetime import date, datetime
import uuid
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.models import Availability, AvailabilityStatus, Booking, BookingStatus, Restaurant, Review, Role, Subscription, SubscriptionStatus, User


def dashboard_metrics(session: Session) -> dict[str, float | int]:
    bookings = session.scalars(select(Booking)).all()
    users = session.scalar(select(func.count(User.id))) or 0
    restaurants = session.scalar(select(func.count(Restaurant.id)).where(Restaurant.is_active.is_(True))) or 0
    active_slots = session.scalar(select(func.count(Availability.id)).where(Availability.status == AvailabilityStatus.available)) or 0
    revenue = sum(b.platform_fee for b in bookings if b.status in {BookingStatus.confirmed, BookingStatus.completed})
    gbv = sum(b.total_amount for b in bookings if b.status in {BookingStatus.confirmed, BookingStatus.completed})
    return {
        "restaurants": restaurants,
        "users": users,
        "active_slots": active_slots,
        "bookings": len(bookings),
        "platform_revenue": round(revenue, 2),
        "gbv": round(gbv, 2),
    }


def bookings_dataframe(session: Session) -> pd.DataFrame:
    rows = []
    bookings = session.scalars(
        select(Booking).options(joinedload(Booking.customer), joinedload(Booking.availability).joinedload(Availability.restaurant)).order_by(Booking.booking_date.desc())
    ).all()
    for b in bookings:
        rows.append(
            {
                "Codice": b.booking_code,
                "Cliente": b.customer.full_name,
                "Ristorante": b.availability.restaurant.name,
                "Citta": b.availability.city,
                "Data servizio": b.availability.service_date.isoformat(),
                "Persone": b.party_size,
                "Totale": b.total_amount,
                "Fee": b.platform_fee,
                "Stato": b.status.value,
            }
        )
    return pd.DataFrame(rows)


def revenue_timeseries(session: Session) -> pd.DataFrame:
    df = bookings_dataframe(session)
    if df.empty:
        return pd.DataFrame(columns=["Data servizio", "Fee", "Totale"])
    return df.groupby("Data servizio", as_index=False)[["Fee", "Totale"]].sum()


def restaurants_dataframe(session: Session) -> pd.DataFrame:
    rows = []
    restaurants = session.scalars(select(Restaurant).order_by(Restaurant.city, Restaurant.name)).all()
    for r in restaurants:
        avg_rating = session.scalar(select(func.avg(Review.rating)).where(Review.restaurant_id == r.id))
        rows.append({"ID": r.id, "Nome": r.name, "Alias secret": r.secret_alias, "Citta": r.city, "Area": r.area, "Cucina": r.cuisine, "Stelle": r.michelin_stars, "Rating": round(avg_rating or 0, 1), "Attivo": r.is_active})
    return pd.DataFrame(rows)


def availability_dataframe(session: Session, only_available: bool = False) -> pd.DataFrame:
    stmt = select(Availability).options(joinedload(Availability.restaurant)).order_by(Availability.service_date, Availability.service_time)
    if only_available:
        stmt = stmt.where(Availability.status == AvailabilityStatus.available, Availability.service_date >= date.today())
    rows = []
    for a in session.scalars(stmt).all():
        rows.append({"ID": a.id, "Alias secret": a.restaurant.secret_alias, "Ristorante": a.restaurant.name, "Citta": a.city, "Cucina": a.cuisine, "Data": a.service_date.isoformat(), "Ora": a.service_time, "Persone": a.party_size, "Prezzo persona": a.price_per_person, "Fee": a.restaurant_fee, "Menu": a.menu_title, "Stato": a.status.value})
    return pd.DataFrame(rows)


def book_slot(session: Session, user_id: int, availability_id: int, notes: str = "") -> Booking:
    slot = session.scalar(select(Availability).where(Availability.id == availability_id).with_for_update())
    if not slot or slot.status != AvailabilityStatus.available:
        raise ValueError("Disponibilità non più prenotabile")
    slot.status = AvailabilityStatus.booked
    booking = Booking(
        customer_id=user_id,
        availability=slot,
        booking_code=f"SSR-{uuid.uuid4().hex[:8].upper()}",
        party_size=slot.party_size,
        total_amount=slot.party_size * slot.price_per_person,
        platform_fee=slot.restaurant_fee,
        status=BookingStatus.confirmed,
        booking_date=datetime.utcnow(),
        notes=notes.strip() or None,
    )
    session.add(booking)
    session.flush()
    return booking


def create_availability(session: Session, restaurant_id: int, service_date: date, service_time: str, party_size: int, price_per_person: float, restaurant_fee: float, menu_title: str, menu_description: str) -> Availability:
    restaurant = session.get(Restaurant, restaurant_id)
    if not restaurant:
        raise ValueError("Ristorante non trovato")
    slot = Availability(
        restaurant=restaurant,
        service_date=service_date,
        service_time=service_time,
        city=restaurant.city,
        cuisine=restaurant.cuisine,
        party_size=party_size,
        price_per_person=price_per_person,
        restaurant_fee=restaurant_fee,
        menu_title=menu_title,
        menu_description=menu_description,
        status=AvailabilityStatus.available,
    )
    session.add(slot)
    session.flush()
    return slot


def active_subscription(session: Session, user_id: int) -> bool:
    today = date.today()
    sub = session.scalar(select(Subscription).where(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.active, Subscription.expires_at >= today))
    return sub is not None
