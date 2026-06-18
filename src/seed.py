from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth import create_user
from src.models import Availability, Booking, BookingStatus, Restaurant, Review, Role, Subscription, SubscriptionStatus, User


def seed_demo_data(session: Session) -> None:
    if session.scalar(select(User).limit(1)):
        return

    admin = create_user(session, "Admin Secret Star", "admin@secretstar.local", "Admin123!", Role.admin)
    manager = create_user(session, "Restaurant Manager", "manager@secretstar.local", "Manager123!", Role.restaurant)
    customer = create_user(session, "Cliente Premium", "cliente@secretstar.local", "Cliente123!", Role.customer)

    restaurants = [
        Restaurant(manager=manager, public_code="SSR-MI-001", name="Luce Segreta Milano", secret_alias="Secret Milano Brera", city="Milano", area="Brera", cuisine="Contemporanea", michelin_stars=1, address="Via Brera 12, Milano", description="Fine dining contemporaneo con percorso degustazione stagionale."),
        Restaurant(manager=manager, public_code="SSR-CO-002", name="Stella sul Lago", secret_alias="Secret Lago di Como", city="Como", area="Lago di Como", cuisine="Italiana creativa", michelin_stars=1, address="Lungo Lago 8, Como", description="Esperienza premium con vista lago e menu territoriale."),
        Restaurant(manager=manager, public_code="SSR-BG-003", name="Orizzonte Gourmet", secret_alias="Secret Bergamo Alta", city="Bergamo", area="Città Alta", cuisine="Tradizionale evoluta", michelin_stars=2, address="Piazza Vecchia 4, Bergamo", description="Cucina lombarda reinterpretata in chiave stellata."),
    ]
    session.add_all(restaurants)
    session.flush()

    today = date.today()
    for index, restaurant in enumerate(restaurants):
        for day_offset in range(0, 5):
            session.add(
                Availability(
                    restaurant=restaurant,
                    service_date=today + timedelta(days=day_offset),
                    service_time="20:30",
                    city=restaurant.city,
                    cuisine=restaurant.cuisine,
                    party_size=2 if day_offset % 2 == 0 else 4,
                    price_per_person=110.0 + index * 20,
                    restaurant_fee=30.0 if index < 2 else 50.0,
                    menu_title="Percorso Secret Star",
                    menu_description="Tavolo e menu degustazione selezionato, ristorante rivelato dopo la conferma.",
                )
            )
    session.flush()

    first_slot = session.scalar(select(Availability).limit(1))
    if first_slot:
        first_slot.status = "booked"
        booking = Booking(
            customer=customer,
            availability=first_slot,
            booking_code="SSR-DEMO-001",
            party_size=first_slot.party_size,
            total_amount=first_slot.party_size * first_slot.price_per_person,
            platform_fee=first_slot.restaurant_fee,
            status=BookingStatus.completed,
            notes="Prenotazione demo completata.",
        )
        session.add(booking)
        session.flush()
        session.add(Review(booking=booking, restaurant=first_slot.restaurant, customer=customer, rating=5, comment="Esperienza eccellente e gestione impeccabile."))

    session.add(
        Subscription(
            user=customer,
            plan_name="Premium Monthly",
            monthly_price=3.99,
            status=SubscriptionStatus.active,
            starts_at=today,
            expires_at=today + timedelta(days=30),
        )
    )
