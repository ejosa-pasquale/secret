from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None
import streamlit as st
from sqlalchemy import select

from src.auth import authenticate, can_manage_restaurant, create_user
from src.database import get_session, init_db
from src.models import Role, Restaurant, User
from src.queries import (
    active_subscription,
    availability_dataframe,
    book_slot,
    bookings_dataframe,
    create_availability,
    dashboard_metrics,
    restaurants_dataframe,
    revenue_timeseries,
)
from src.seed import seed_demo_data
from src.ui import hero, inject_css, require_login

st.set_page_config(page_title="Secret Star Restaurant", page_icon="⭐", layout="wide")
inject_css()
init_db()
with get_session() as session:
    seed_demo_data(session)


def login_box() -> None:
    hero("Diamo nuova vita ai tavoli più esclusivi", "Marketplace premium per disponibilità last-minute nei ristoranti stellati.")
    tab_login, tab_register = st.tabs(["Login", "Registrazione cliente"])
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", value="admin@secretstar.local")
            password = st.text_input("Password", type="password", value="Admin123!")
            submitted = st.form_submit_button("Entra")
        if submitted:
            with get_session() as session:
                user = authenticate(session, email, password)
                if user:
                    st.session_state.user = {"id": user.id, "name": user.full_name, "email": user.email, "role": user.role.value}
                    st.success("Login effettuato")
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
        st.info("Demo: admin@secretstar.local / Admin123! | manager@secretstar.local / Manager123! | cliente@secretstar.local / Cliente123!")
    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input("Nome completo")
            email = st.text_input("Email nuova")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Crea account")
        if submitted:
            try:
                if len(password) < 8:
                    st.error("La password deve contenere almeno 8 caratteri")
                else:
                    with get_session() as session:
                        create_user(session, full_name, email, password, Role.customer)
                    st.success("Account creato. Ora puoi effettuare il login.")
            except Exception as exc:
                st.error(str(exc))


def sidebar() -> str:
    user = st.session_state.user
    st.sidebar.title("⭐ Secret Star")
    st.sidebar.caption(f"{user['name']} · {user['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    pages = ["Dashboard", "Marketplace", "Prenotazioni", "Ristoranti", "Disponibilità", "Abbonamenti", "Review"]
    if user["role"] == "customer":
        pages = ["Marketplace", "Prenotazioni", "Abbonamenti", "Review"]
    return st.sidebar.radio("Menu", pages)


def dashboard_page() -> None:
    hero("Dashboard operativa", "KPI, ricavi, andamento vendite e qualità marketplace.")
    with get_session() as session:
        metrics = dashboard_metrics(session)
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Ristoranti", metrics["restaurants"])
        c2.metric("Utenti", metrics["users"])
        c3.metric("Slot attivi", metrics["active_slots"])
        c4.metric("Prenotazioni", metrics["bookings"])
        c5.metric("Ricavi piattaforma", f"€ {metrics['platform_revenue']:,.0f}")
        c6.metric("GBV", f"€ {metrics['gbv']:,.0f}")
        ts = revenue_timeseries(session)
        bookings = bookings_dataframe(session)
    if not ts.empty:
        chart_data = ts.set_index("Data servizio")[["Fee", "Totale"]]
        if px is not None:
            fig = px.line(ts, x="Data servizio", y=["Fee", "Totale"], markers=True, title="Andamento ricavi e valore transato")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(chart_data)
    st.subheader("Ultime prenotazioni")
    st.dataframe(bookings, use_container_width=True, hide_index=True)


def marketplace_page() -> None:
    hero("Marketplace last-minute", "Scegli taste, location ed esperienza. Il ristorante resta secret fino alla conferma.")
    if not require_login():
        return
    with get_session() as session:
        has_sub = active_subscription(session, st.session_state.user["id"])
        df = availability_dataframe(session, only_available=True)
    if not has_sub:
        st.warning("Serve una membership attiva per prenotare. Vai in Abbonamenti per attivarla.")
    if df.empty:
        st.info("Nessuna disponibilità attiva al momento.")
        return
    col1, col2, col3 = st.columns(3)
    city = col1.selectbox("Location", ["Tutte"] + sorted(df["Citta"].unique().tolist()))
    cuisine = col2.selectbox("Taste", ["Tutte"] + sorted(df["Cucina"].unique().tolist()))
    party = col3.selectbox("Persone", ["Tutte"] + sorted(df["Persone"].unique().tolist()))
    filtered = df.copy()
    if city != "Tutte":
        filtered = filtered[filtered["Citta"] == city]
    if cuisine != "Tutte":
        filtered = filtered[filtered["Cucina"] == cuisine]
    if party != "Tutte":
        filtered = filtered[filtered["Persone"] == party]
    for _, row in filtered.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.subheader(row["Alias secret"])
            c1.write(f"{row['Citta']} · {row['Cucina']} · {row['Data']} alle {row['Ora']}")
            c1.caption("Nome e indirizzo del ristorante saranno rivelati dopo la prenotazione.")
            c2.metric("Persone", int(row["Persone"]))
            c2.metric("Prezzo/persona", f"€ {row['Prezzo persona']:.0f}")
            c3.metric("Totale", f"€ {row['Prezzo persona'] * row['Persone']:.0f}")
            note = st.text_input("Note allergie/preferenze", key=f"note_{row['ID']}")
            if st.button("Prenota ora", key=f"book_{row['ID']}", disabled=not has_sub):
                try:
                    with get_session() as session:
                        booking = book_slot(session, st.session_state.user["id"], int(row["ID"]), note)
                    st.success(f"Prenotazione confermata. Codice {booking.booking_code}. Il ristorante è ora visibile nella sezione Prenotazioni.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def bookings_page() -> None:
    hero("Prenotazioni", "Gestione delle prenotazioni confermate, completate e cancellate.")
    with get_session() as session:
        df = bookings_dataframe(session)
    if df.empty:
        st.info("Nessuna prenotazione presente.")
        return
    query = st.text_input("Cerca per codice, cliente, ristorante o città")
    if query:
        mask = df.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
        df = df[mask]
    st.dataframe(df, use_container_width=True, hide_index=True)


def restaurants_page() -> None:
    hero("Ristoranti partner", "Anagrafica ristoranti stellati, aree pilota e rating qualità.")
    if not can_manage_restaurant(st.session_state.user["role"]):
        st.error("Permesso insufficiente")
        return
    with get_session() as session:
        df = restaurants_dataframe(session)
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Aggiungi ristorante"):
        with st.form("restaurant_form"):
            name = st.text_input("Nome reale")
            alias = st.text_input("Alias secret")
            city = st.text_input("Città", value="Milano")
            area = st.text_input("Area", value="Brera")
            cuisine = st.text_input("Cucina", value="Contemporanea")
            stars = st.number_input("Stelle Michelin", 1, 3, 1)
            address = st.text_input("Indirizzo")
            description = st.text_area("Descrizione")
            submitted = st.form_submit_button("Salva")
        if submitted:
            with get_session() as session:
                manager = session.scalar(select(User).where(User.role == Role.restaurant))
                session.add(Restaurant(manager=manager, public_code=f"SSR-{city[:2].upper()}-{len(df)+1:03d}", name=name, secret_alias=alias, city=city, area=area, cuisine=cuisine, michelin_stars=int(stars), address=address, description=description))
            st.success("Ristorante creato")
            st.rerun()


def availability_page() -> None:
    hero("Disponibilità entro le 10:00", "Pubblicazione controllata dei tavoli last-minute monetizzabili.")
    if not can_manage_restaurant(st.session_state.user["role"]):
        st.error("Permesso insufficiente")
        return
    with get_session() as session:
        df = availability_dataframe(session)
        restaurants = session.scalars(select(Restaurant).where(Restaurant.is_active.is_(True)).order_by(Restaurant.name)).all()
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Pubblica nuova disponibilità"):
        with st.form("availability_form"):
            restaurant_map = {f"{r.name} · {r.city}": r.id for r in restaurants}
            selected = st.selectbox("Ristorante", list(restaurant_map.keys()))
            service_date = st.date_input("Data servizio", value=date.today())
            service_time = st.text_input("Ora", value="20:30")
            party_size = st.selectbox("Persone", [2, 4])
            price = st.number_input("Prezzo per persona", min_value=50.0, value=120.0, step=10.0)
            fee = st.selectbox("Fee ristorante", [30.0, 50.0])
            menu_title = st.text_input("Titolo menu", value="Percorso Secret Star")
            menu_description = st.text_area("Descrizione menu", value="Menu degustazione premium con tavolo secret.")
            submitted = st.form_submit_button("Pubblica")
        if submitted:
            try:
                with get_session() as session:
                    create_availability(session, restaurant_map[selected], service_date, service_time, int(party_size), float(price), float(fee), menu_title, menu_description)
                st.success("Disponibilità pubblicata")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def subscriptions_page() -> None:
    hero("Membership", "Modello premium: €3,99 al mese o piano annuale per accedere alle disponibilità selezionate.")
    with get_session() as session:
        has_sub = active_subscription(session, st.session_state.user["id"])
    if has_sub:
        st.success("Membership attiva")
    else:
        st.warning("Membership non attiva")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Premium Monthly")
        st.metric("Prezzo", "€3,99/mese")
        if st.button("Attiva monthly"):
            from src.models import Subscription, SubscriptionStatus
            with get_session() as session:
                session.add(Subscription(user_id=st.session_state.user["id"], plan_name="Premium Monthly", monthly_price=3.99, status=SubscriptionStatus.active, starts_at=date.today(), expires_at=date.today() + timedelta(days=30)))
            st.success("Membership monthly attivata")
            st.rerun()
    with col2:
        st.subheader("Premium Annual")
        st.metric("Prezzo", "€50/anno")
        if st.button("Attiva annual"):
            from src.models import Subscription, SubscriptionStatus
            with get_session() as session:
                session.add(Subscription(user_id=st.session_state.user["id"], plan_name="Premium Annual", monthly_price=50.0 / 12, status=SubscriptionStatus.active, starts_at=date.today(), expires_at=date.today() + timedelta(days=365)))
            st.success("Membership annuale attivata")
            st.rerun()


def reviews_page() -> None:
    hero("Review e qualità", "Raccolta feedback per preservare posizionamento premium e qualità della clientela.")
    with get_session() as session:
        from src.models import Booking, BookingStatus, Review
        completed = session.scalars(select(Booking).where(Booking.customer_id == st.session_state.user["id"], Booking.status == BookingStatus.completed)).all()
        reviews = session.scalars(select(Review)).all()
    if reviews:
        rows = [{"Ristorante": r.restaurant.name, "Cliente": r.customer.full_name, "Rating": r.rating, "Commento": r.comment} for r in reviews]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nessuna review ancora presente.")
    if completed:
        with st.expander("Lascia una review"):
            with st.form("review_form"):
                booking_map = {f"{b.booking_code} · {b.availability.restaurant.name}": b.id for b in completed if not b.review}
                if booking_map:
                    selected = st.selectbox("Prenotazione", list(booking_map.keys()))
                    rating = st.slider("Rating", 1, 5, 5)
                    comment = st.text_area("Commento")
                    submitted = st.form_submit_button("Invia review")
                    if submitted:
                        with get_session() as session:
                            b = session.get(Booking, booking_map[selected])
                            session.add(Review(booking_id=b.id, restaurant_id=b.availability.restaurant_id, customer_id=st.session_state.user["id"], rating=int(rating), comment=comment))
                        st.success("Review inviata")
                        st.rerun()
                else:
                    st.info("Non ci sono prenotazioni completate da recensire.")


if "user" not in st.session_state:
    login_box()
else:
    selected_page = sidebar()
    if selected_page == "Dashboard":
        dashboard_page()
    elif selected_page == "Marketplace":
        marketplace_page()
    elif selected_page == "Prenotazioni":
        bookings_page()
    elif selected_page == "Ristoranti":
        restaurants_page()
    elif selected_page == "Disponibilità":
        availability_page()
    elif selected_page == "Abbonamenti":
        subscriptions_page()
    elif selected_page == "Review":
        reviews_page()
