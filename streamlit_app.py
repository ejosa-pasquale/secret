from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import streamlit as st

APP_NAME = "Secret Star Restaurant"
DB_PATH = Path(os.getenv("SECRET_STAR_DB", "data/secret_star_streamlit.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title=APP_NAME, page_icon="⭐", layout="wide")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with closing(connect()) as conn:
        conn.execute(sql, params)
        conn.commit()


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with closing(connect()) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with closing(connect()) as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, salt), stored)


def init_db() -> None:
    with closing(connect()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','restaurant','customer')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);

            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_id INTEGER,
                public_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                secret_alias TEXT NOT NULL,
                city TEXT NOT NULL,
                area TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                michelin_stars INTEGER NOT NULL DEFAULT 1,
                address TEXT NOT NULL,
                description TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(manager_id) REFERENCES users(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS ix_restaurants_city ON restaurants(city);
            CREATE INDEX IF NOT EXISTS ix_restaurants_cuisine ON restaurants(cuisine);

            CREATE TABLE IF NOT EXISTS availabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                service_date TEXT NOT NULL,
                service_time TEXT NOT NULL,
                city TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                party_size INTEGER NOT NULL,
                price_per_person REAL NOT NULL,
                restaurant_fee REAL NOT NULL,
                menu_title TEXT NOT NULL,
                menu_description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','booked','expired','cancelled')),
                published_at TEXT NOT NULL,
                UNIQUE(restaurant_id, service_date, service_time),
                FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS ix_availability_search ON availabilities(service_date, city, cuisine, status);

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                availability_id INTEGER NOT NULL UNIQUE,
                booking_code TEXT NOT NULL UNIQUE,
                party_size INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                platform_fee REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled','completed','no_show')),
                booking_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(availability_id) REFERENCES availabilities(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS ix_bookings_status ON bookings(status);
            CREATE INDEX IF NOT EXISTS ix_bookings_customer ON bookings(customer_id);

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                monthly_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','expired','cancelled')),
                starts_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS ix_subscriptions_user ON subscriptions(user_id, status, expires_at);

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL UNIQUE,
                restaurant_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                FOREIGN KEY(restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
                FOREIGN KEY(customer_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()


def create_user(full_name: str, email: str, password: str, role: str) -> None:
    execute(
        "INSERT INTO users(full_name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
        (full_name.strip(), email.lower().strip(), hash_password(password), role, datetime.utcnow().isoformat()),
    )


def seed_demo_data() -> None:
    if fetch_one("SELECT id FROM users LIMIT 1"):
        return
    create_user("Admin Secret Star", "admin@secretstar.local", "Admin123!", "admin")
    create_user("Restaurant Manager", "manager@secretstar.local", "Manager123!", "restaurant")
    create_user("Cliente Premium", "cliente@secretstar.local", "Cliente123!", "customer")
    manager = fetch_one("SELECT id FROM users WHERE email=?", ("manager@secretstar.local",))
    customer = fetch_one("SELECT id FROM users WHERE email=?", ("cliente@secretstar.local",))
    manager_id = manager["id"] if manager else None
    restaurants = [
        (manager_id, "SSR-MI-001", "Luce Segreta Milano", "Secret Milano Brera", "Milano", "Brera", "Contemporanea", 1, "Via Brera 12, Milano", "Fine dining contemporaneo con menu degustazione stagionale."),
        (manager_id, "SSR-CO-002", "Stella sul Lago", "Secret Lago di Como", "Como", "Lago di Como", "Italiana creativa", 1, "Lungo Lago 8, Como", "Esperienza premium vista lago con cucina territoriale."),
        (manager_id, "SSR-BG-003", "Orizzonte Gourmet", "Secret Bergamo Alta", "Bergamo", "Citta Alta", "Tradizionale evoluta", 2, "Piazza Vecchia 4, Bergamo", "Cucina lombarda reinterpretata in chiave stellata."),
        (manager_id, "SSR-FC-004", "Cantina Stellata", "Secret Franciacorta", "Brescia", "Franciacorta", "Wine pairing", 1, "Via Vigne 7, Brescia", "Percorso gourmet con pairing vini premium."),
    ]
    with closing(connect()) as conn:
        conn.executemany(
            """INSERT INTO restaurants(manager_id,public_code,name,secret_alias,city,area,cuisine,michelin_stars,address,description,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            [r + (datetime.utcnow().isoformat(),) for r in restaurants],
        )
        conn.commit()
    today = date.today()
    rest_rows = fetch_all("SELECT * FROM restaurants ORDER BY id")
    for index, restaurant in enumerate(rest_rows):
        for offset in range(0, 7):
            execute(
                """INSERT OR IGNORE INTO availabilities(restaurant_id,service_date,service_time,city,cuisine,party_size,price_per_person,restaurant_fee,menu_title,menu_description,status,published_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    restaurant["id"],
                    (today + timedelta(days=offset)).isoformat(),
                    "20:30",
                    restaurant["city"],
                    restaurant["cuisine"],
                    2 if offset % 2 == 0 else 4,
                    110.0 + index * 15,
                    30.0 if index < 2 else 50.0,
                    "Percorso Secret Star",
                    "Tavolo e menu degustazione selezionato. Nome ristorante rivelato dopo la conferma.",
                    "available",
                    datetime.utcnow().isoformat(),
                ),
            )
    first_slot = fetch_one("SELECT * FROM availabilities ORDER BY id LIMIT 1")
    if first_slot and customer:
        code = "SSR-DEMO-001"
        execute("UPDATE availabilities SET status='booked' WHERE id=?", (first_slot["id"],))
        execute(
            """INSERT INTO bookings(customer_id,availability_id,booking_code,party_size,total_amount,platform_fee,status,booking_date,notes)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (customer["id"], first_slot["id"], code, first_slot["party_size"], first_slot["party_size"] * first_slot["price_per_person"], first_slot["restaurant_fee"], "completed", datetime.utcnow().isoformat(), "Prenotazione demo completata."),
        )
        booking = fetch_one("SELECT id FROM bookings WHERE booking_code=?", (code,))
        if booking:
            execute(
                "INSERT INTO reviews(booking_id,restaurant_id,customer_id,rating,comment,created_at) VALUES(?,?,?,?,?,?)",
                (booking["id"], first_slot["restaurant_id"], customer["id"], 5, "Esperienza eccellente e gestione impeccabile.", datetime.utcnow().isoformat()),
            )
        execute(
            "INSERT INTO subscriptions(user_id,plan_name,monthly_price,status,starts_at,expires_at) VALUES(?,?,?,?,?,?)",
            (customer["id"], "Premium Monthly", 3.99, "active", today.isoformat(), (today + timedelta(days=30)).isoformat()),
        )


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container {padding-top:1.4rem; max-width:1280px;}
        .hero {background:linear-gradient(135deg,#10251f,#0f7b5c); color:white; padding:28px; border-radius:24px; margin-bottom:18px;}
        .hero h1 {margin:0; font-size:2.2rem;}
        .hero p {font-size:1rem; opacity:.92; margin-bottom:0;}
        .pill {display:inline-block; padding:5px 11px; border-radius:999px; background:#e8fff4; color:#0f7b5c; font-weight:800; font-size:.78rem; margin-bottom:10px;}
        div[data-testid="stSidebar"] {background:#10251f;}
        .stButton > button {border-radius:12px; font-weight:700;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero'><span class='pill'>Secret Star Restaurant</span><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    user = fetch_one("SELECT * FROM users WHERE email=? AND is_active=1", (email.lower().strip(),))
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def active_subscription(user_id: int) -> bool:
    return fetch_one("SELECT id FROM subscriptions WHERE user_id=? AND status='active' AND expires_at>=?", (user_id, date.today().isoformat())) is not None


def table(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return fetch_all(sql, params)


def login_page() -> None:
    hero("Diamo nuova vita ai tavoli più esclusivi", "Marketplace premium per disponibilita last-minute nei ristoranti stellati.")
    tab1, tab2 = st.tabs(["Login", "Registrazione cliente"])
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", value="admin@secretstar.local")
            password = st.text_input("Password", type="password", value="Admin123!")
            submitted = st.form_submit_button("Entra")
        if submitted:
            user = authenticate(email, password)
            if user:
                st.session_state.user = {"id": user["id"], "name": user["full_name"], "email": user["email"], "role": user["role"]}
                st.success("Login effettuato")
                st.rerun()
            else:
                st.error("Credenziali non valide")
        st.info("Demo: admin@secretstar.local / Admin123! | manager@secretstar.local / Manager123! | cliente@secretstar.local / Cliente123!")
    with tab2:
        with st.form("register_form"):
            full_name = st.text_input("Nome completo")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Crea account")
        if submitted:
            if not full_name or not email or len(password) < 8:
                st.error("Compila tutti i campi. La password deve avere almeno 8 caratteri.")
            else:
                try:
                    create_user(full_name, email, password, "customer")
                    st.success("Account creato. Ora puoi effettuare il login.")
                except sqlite3.IntegrityError:
                    st.error("Email gia registrata")


def sidebar() -> str:
    user = st.session_state.user
    st.sidebar.title("⭐ Secret Star")
    st.sidebar.caption(f"{user['name']} · {user['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    pages = ["Dashboard", "Marketplace", "Prenotazioni", "Ristoranti", "Disponibilita", "Abbonamenti", "Review"]
    if user["role"] == "customer":
        pages = ["Marketplace", "Prenotazioni", "Abbonamenti", "Review"]
    return st.sidebar.radio("Menu", pages)


def dashboard_page() -> None:
    hero("Dashboard operativa", "KPI, ricavi, andamento vendite, ordini, clienti, prodotti e incassi.")
    restaurants = fetch_one("SELECT COUNT(*) AS n FROM restaurants")["n"]
    users = fetch_one("SELECT COUNT(*) AS n FROM users")["n"]
    active_slots = fetch_one("SELECT COUNT(*) AS n FROM availabilities WHERE status='available' AND service_date>=?", (date.today().isoformat(),))["n"]
    bookings = fetch_one("SELECT COUNT(*) AS n FROM bookings")["n"]
    revenue = fetch_one("SELECT COALESCE(SUM(platform_fee),0) AS n FROM bookings WHERE status IN ('confirmed','completed')")["n"]
    gbv = fetch_one("SELECT COALESCE(SUM(total_amount),0) AS n FROM bookings WHERE status IN ('confirmed','completed')")["n"]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Ristoranti", restaurants)
    c2.metric("Utenti", users)
    c3.metric("Slot attivi", active_slots)
    c4.metric("Prenotazioni", bookings)
    c5.metric("Ricavi", f"€ {revenue:,.0f}")
    c6.metric("GBV", f"€ {gbv:,.0f}")
    rows = fetch_all(
        """SELECT a.service_date AS data, SUM(b.platform_fee) AS fee, SUM(b.total_amount) AS totale
        FROM bookings b JOIN availabilities a ON a.id=b.availability_id
        WHERE b.status IN ('confirmed','completed') GROUP BY a.service_date ORDER BY a.service_date"""
    )
    if rows:
        chart = {row["data"]: {"Fee": row["fee"], "Totale": row["totale"]} for row in rows}
        st.line_chart(chart)
    st.subheader("Ultime prenotazioni")
    st.dataframe(bookings_rows(), use_container_width=True, hide_index=True)


def marketplace_rows() -> list[dict[str, Any]]:
    return fetch_all(
        """SELECT a.id AS ID, r.secret_alias AS 'Alias secret', r.name AS Ristorante, a.city AS Citta, a.cuisine AS Cucina,
        a.service_date AS Data, a.service_time AS Ora, a.party_size AS Persone, a.price_per_person AS 'Prezzo persona',
        a.restaurant_fee AS Fee, a.menu_title AS Menu, a.status AS Stato
        FROM availabilities a JOIN restaurants r ON r.id=a.restaurant_id
        WHERE a.status='available' AND a.service_date>=? ORDER BY a.service_date, a.service_time""",
        (date.today().isoformat(),),
    )


def marketplace_page() -> None:
    hero("Marketplace last-minute", "Scegli taste, location ed esperienza. Il ristorante resta secret fino alla conferma.")
    user = st.session_state.user
    has_sub = active_subscription(user["id"])
    if not has_sub:
        st.warning("Serve una membership attiva per prenotare. Vai in Abbonamenti per attivarla.")
    rows = marketplace_rows()
    if not rows:
        st.info("Nessuna disponibilita attiva al momento.")
        return
    cities = ["Tutte"] + sorted({r["Citta"] for r in rows})
    cuisines = ["Tutte"] + sorted({r["Cucina"] for r in rows})
    col1, col2, col3 = st.columns(3)
    city = col1.selectbox("Location", cities)
    cuisine = col2.selectbox("Taste", cuisines)
    party = col3.selectbox("Persone", ["Tutte", 2, 4])
    filtered = [r for r in rows if (city == "Tutte" or r["Citta"] == city) and (cuisine == "Tutte" or r["Cucina"] == cuisine) and (party == "Tutte" or r["Persone"] == party)]
    for row in filtered:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.subheader(row["Alias secret"])
            c1.write(f"{row['Citta']} · {row['Cucina']} · {row['Data']} alle {row['Ora']}")
            c1.caption("Nome e indirizzo saranno rivelati dopo la prenotazione.")
            c2.metric("Persone", int(row["Persone"]))
            c2.metric("Prezzo/persona", f"€ {row['Prezzo persona']:.0f}")
            c3.metric("Totale", f"€ {row['Prezzo persona'] * row['Persone']:.0f}")
            note = st.text_input("Note allergie/preferenze", key=f"note_{row['ID']}")
            if st.button("Prenota ora", key=f"book_{row['ID']}", disabled=not has_sub):
                book_slot(user["id"], int(row["ID"]), note)
                st.success("Prenotazione confermata. Ora il ristorante e visibile nella sezione Prenotazioni.")
                st.rerun()


def book_slot(user_id: int, availability_id: int, notes: str) -> None:
    with closing(connect()) as conn:
        slot = conn.execute("SELECT * FROM availabilities WHERE id=?", (availability_id,)).fetchone()
        if not slot or slot["status"] != "available":
            raise RuntimeError("Disponibilita non piu prenotabile")
        code = f"SSR-{secrets.token_hex(4).upper()}"
        conn.execute("UPDATE availabilities SET status='booked' WHERE id=?", (availability_id,))
        conn.execute(
            """INSERT INTO bookings(customer_id,availability_id,booking_code,party_size,total_amount,platform_fee,status,booking_date,notes)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (user_id, availability_id, code, slot["party_size"], slot["party_size"] * slot["price_per_person"], slot["restaurant_fee"], "confirmed", datetime.utcnow().isoformat(), notes.strip() or None),
        )
        conn.commit()


def bookings_rows() -> list[dict[str, Any]]:
    user = st.session_state.get("user")
    where = ""
    params: tuple[Any, ...] = ()
    if user and user["role"] == "customer":
        where = "WHERE b.customer_id=?"
        params = (user["id"],)
    return fetch_all(
        f"""SELECT b.booking_code AS Codice, u.full_name AS Cliente, r.name AS Ristorante, r.address AS Indirizzo,
        a.city AS Citta, a.service_date AS 'Data servizio', a.service_time AS Ora, b.party_size AS Persone,
        b.total_amount AS Totale, b.platform_fee AS Fee, b.status AS Stato
        FROM bookings b
        JOIN users u ON u.id=b.customer_id
        JOIN availabilities a ON a.id=b.availability_id
        JOIN restaurants r ON r.id=a.restaurant_id
        {where}
        ORDER BY b.booking_date DESC""",
        params,
    )


def bookings_page() -> None:
    hero("Prenotazioni", "Gestione delle prenotazioni confermate, completate e cancellate.")
    rows = bookings_rows()
    query = st.text_input("Cerca")
    if query:
        rows = [r for r in rows if query.lower() in " ".join(str(v).lower() for v in r.values())]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def restaurants_page() -> None:
    hero("Ristoranti partner", "Anagrafica ristoranti stellati, aree pilota e rating qualita.")
    if st.session_state.user["role"] not in {"admin", "restaurant"}:
        st.error("Permesso insufficiente")
        return
    rows = fetch_all("SELECT id AS ID, name AS Nome, secret_alias AS 'Alias secret', city AS Citta, area AS Area, cuisine AS Cucina, michelin_stars AS Stelle, is_active AS Attivo FROM restaurants ORDER BY city, name")
    st.dataframe(rows, use_container_width=True, hide_index=True)
    with st.expander("Aggiungi ristorante"):
        with st.form("restaurant_form"):
            name = st.text_input("Nome reale")
            alias = st.text_input("Alias secret")
            city = st.text_input("Citta", value="Milano")
            area = st.text_input("Area", value="Brera")
            cuisine = st.text_input("Cucina", value="Contemporanea")
            stars = st.number_input("Stelle Michelin", 1, 3, 1)
            address = st.text_input("Indirizzo")
            description = st.text_area("Descrizione")
            submitted = st.form_submit_button("Salva")
        if submitted:
            code = f"SSR-{city[:2].upper()}-{secrets.token_hex(2).upper()}"
            manager = fetch_one("SELECT id FROM users WHERE role='restaurant' LIMIT 1")
            execute(
                """INSERT INTO restaurants(manager_id,public_code,name,secret_alias,city,area,cuisine,michelin_stars,address,description,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                ((manager or {}).get("id"), code, name, alias, city, area, cuisine, int(stars), address, description, datetime.utcnow().isoformat()),
            )
            st.success("Ristorante creato")
            st.rerun()


def availability_page() -> None:
    hero("Disponibilita entro le 10:00", "Pubblicazione controllata dei tavoli last-minute monetizzabili.")
    if st.session_state.user["role"] not in {"admin", "restaurant"}:
        st.error("Permesso insufficiente")
        return
    rows = fetch_all(
        """SELECT a.id AS ID, r.name AS Ristorante, r.secret_alias AS 'Alias secret', a.city AS Citta, a.cuisine AS Cucina,
        a.service_date AS Data, a.service_time AS Ora, a.party_size AS Persone, a.price_per_person AS 'Prezzo persona',
        a.restaurant_fee AS Fee, a.menu_title AS Menu, a.status AS Stato
        FROM availabilities a JOIN restaurants r ON r.id=a.restaurant_id ORDER BY a.service_date DESC, a.service_time"""
    )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    restaurants = fetch_all("SELECT id, name, city FROM restaurants WHERE is_active=1 ORDER BY name")
    with st.expander("Pubblica nuova disponibilita"):
        with st.form("availability_form"):
            labels = {f"{r['name']} · {r['city']}": r["id"] for r in restaurants}
            selected = st.selectbox("Ristorante", list(labels.keys())) if labels else None
            service_date = st.date_input("Data servizio", value=date.today())
            service_time = st.text_input("Ora", value="20:30")
            party_size = st.selectbox("Persone", [2, 4])
            price = st.number_input("Prezzo per persona", min_value=50.0, value=120.0, step=10.0)
            fee = st.selectbox("Fee ristorante", [30.0, 50.0])
            menu_title = st.text_input("Titolo menu", value="Percorso Secret Star")
            menu_description = st.text_area("Descrizione menu", value="Menu degustazione premium con tavolo secret.")
            submitted = st.form_submit_button("Pubblica")
        if submitted and selected:
            r = fetch_one("SELECT * FROM restaurants WHERE id=?", (labels[selected],))
            try:
                execute(
                    """INSERT INTO availabilities(restaurant_id,service_date,service_time,city,cuisine,party_size,price_per_person,restaurant_fee,menu_title,menu_description,status,published_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r["id"], service_date.isoformat(), service_time, r["city"], r["cuisine"], int(party_size), float(price), float(fee), menu_title, menu_description, "available", datetime.utcnow().isoformat()),
                )
                st.success("Disponibilita pubblicata")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Esiste gia uno slot per questo ristorante alla stessa data e ora.")


def subscriptions_page() -> None:
    hero("Membership", "€3,99 al mese oppure piano annuale da €50 per accedere alle disponibilita selezionate.")
    user = st.session_state.user
    if active_subscription(user["id"]):
        st.success("Membership attiva")
    else:
        st.warning("Membership non attiva")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Premium Monthly")
        st.metric("Prezzo", "€3,99/mese")
        if st.button("Attiva monthly"):
            execute("INSERT INTO subscriptions(user_id,plan_name,monthly_price,status,starts_at,expires_at) VALUES(?,?,?,?,?,?)", (user["id"], "Premium Monthly", 3.99, "active", date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()))
            st.success("Membership monthly attivata")
            st.rerun()
    with col2:
        st.subheader("Premium Annual")
        st.metric("Prezzo", "€50/anno")
        if st.button("Attiva annual"):
            execute("INSERT INTO subscriptions(user_id,plan_name,monthly_price,status,starts_at,expires_at) VALUES(?,?,?,?,?,?)", (user["id"], "Premium Annual", 50.0 / 12, "active", date.today().isoformat(), (date.today() + timedelta(days=365)).isoformat()))
            st.success("Membership annuale attivata")
            st.rerun()


def reviews_page() -> None:
    hero("Review e qualita", "Feedback per preservare posizionamento premium e qualita della clientela.")
    rows = fetch_all(
        """SELECT r.name AS Ristorante, u.full_name AS Cliente, v.rating AS Rating, v.comment AS Commento, v.created_at AS Data
        FROM reviews v JOIN restaurants r ON r.id=v.restaurant_id JOIN users u ON u.id=v.customer_id ORDER BY v.created_at DESC"""
    )
    st.dataframe(rows, use_container_width=True, hide_index=True)
    completed = fetch_all(
        """SELECT b.id, b.booking_code, r.name FROM bookings b
        JOIN availabilities a ON a.id=b.availability_id JOIN restaurants r ON r.id=a.restaurant_id
        LEFT JOIN reviews v ON v.booking_id=b.id
        WHERE b.customer_id=? AND b.status='completed' AND v.id IS NULL""",
        (st.session_state.user["id"],),
    )
    if completed:
        with st.expander("Lascia una review"):
            labels = {f"{b['booking_code']} · {b['name']}": b["id"] for b in completed}
            with st.form("review_form"):
                selected = st.selectbox("Prenotazione", list(labels.keys()))
                rating = st.slider("Rating", 1, 5, 5)
                comment = st.text_area("Commento")
                submitted = st.form_submit_button("Invia review")
            if submitted:
                b = fetch_one("SELECT a.restaurant_id FROM bookings b JOIN availabilities a ON a.id=b.availability_id WHERE b.id=?", (labels[selected],))
                execute("INSERT INTO reviews(booking_id,restaurant_id,customer_id,rating,comment,created_at) VALUES(?,?,?,?,?,?)", (labels[selected], b["restaurant_id"], st.session_state.user["id"], int(rating), comment, datetime.utcnow().isoformat()))
                st.success("Review inviata")
                st.rerun()


def main() -> None:
    init_db()
    seed_demo_data()
    inject_css()
    if "user" not in st.session_state:
        login_page()
        return
    page = sidebar()
    if page == "Dashboard":
        dashboard_page()
    elif page == "Marketplace":
        marketplace_page()
    elif page == "Prenotazioni":
        bookings_page()
    elif page == "Ristoranti":
        restaurants_page()
    elif page == "Disponibilita":
        availability_page()
    elif page == "Abbonamenti":
        subscriptions_page()
    elif page == "Review":
        reviews_page()


if __name__ == "__main__":
    main()
