from __future__ import annotations

import base64
import hashlib
import hmac
import html
import os
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import streamlit as st

APP_TITLE = "Secret Star Restaurant"
DB_PATH = Path(os.environ.get("SECRET_STAR_DB", "secret_star.db"))
ASSET_DIR = Path(__file__).parent / "assets"
PRIMARY = "#137a3b"
MINT = "#5bbda5"
NAVY = "#1d2438"
TEAL = "#1d7f64"
BLUE = "#075197"
LIGHT_GREEN = "#b8ffbb"

st.set_page_config(page_title=APP_TITLE, page_icon="⭐", layout="wide", initial_sidebar_state="expanded")


def image_uri(name: str) -> str:
    path = ASSET_DIR / name
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


def inject_css() -> None:
    hero = image_uri("hero_table.png")
    chef = image_uri("chef.png")
    candle = image_uri("candle_table.png")
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] {{ font-family: Inter, Arial, sans-serif; }}
        .stApp {{ background: #ffffff; color: #202124; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        div[data-testid="stSidebar"] {{ background: {NAVY}; }}
        div[data-testid="stSidebar"] * {{ color: #f7fbff !important; }}
        div[data-testid="stSidebar"] .stButton > button {{
            width: 100%; border-radius: 14px; border: 1px solid rgba(255,255,255,.18);
            background: rgba(255,255,255,.06); color: white; font-weight: 700; padding: .72rem 1rem;
        }}
        div[data-testid="stSidebar"] .stButton > button:hover {{ background: {PRIMARY}; border-color: {PRIMARY}; }}
        .block-container {{ max-width: 1280px; padding-top: 1.3rem; padding-bottom: 4rem; }}
        h1, h2, h3 {{ color: {PRIMARY}; font-weight: 800; letter-spacing: -0.035em; }}
        h1 {{ font-size: clamp(2.2rem, 5vw, 4.6rem); line-height: .98; }}
        h2 {{ font-size: clamp(1.7rem, 3vw, 2.9rem); }}
        .small-muted {{ color: #6b7280; font-size: .96rem; }}
        .hero {{
            display: grid; grid-template-columns: 42% 58%; min-height: 520px; border-radius: 28px;
            overflow: hidden; background: #fff; box-shadow: 0 24px 80px rgba(18,30,46,.12); border: 1px solid #eef0ef;
        }}
        .hero-img {{ background-image: url('{hero}'); background-size: cover; background-position: center; min-height: 520px; }}
        .hero-copy {{ padding: clamp(2rem, 6vw, 5.8rem); display: flex; flex-direction: column; justify-content: center; }}
        .hero-title {{ color:{PRIMARY}; font-size: clamp(2.3rem, 6vw, 5rem); line-height: .98; font-weight: 800; letter-spacing: -.05em; margin-bottom: 1.6rem; }}
        .hero-subtitle {{ font-size: 1.28rem; color:#1f2937; margin-bottom: 1.5rem; }}
        .hero-quote {{ color:{MINT}; font-size: clamp(1.3rem, 2vw, 2rem); font-weight: 800; }}
        .pill-row {{ display:flex; gap:.6rem; flex-wrap:wrap; margin-top:1.4rem; }}
        .pill {{ background:#edf8f2; color:{PRIMARY}; border:1px solid #caebda; padding:.45rem .8rem; border-radius:99px; font-weight:700; font-size:.9rem; }}
        .section {{ margin: 2.5rem 0 1.2rem; }}
        .panel {{ border-radius: 18px; padding: 1.35rem; background:#fff; border:1px solid #e8e8e8; box-shadow:0 12px 30px rgba(18,30,46,.07); }}
        .dark-card {{ background:{NAVY}; color:white; border-radius:14px; padding:1.5rem; min-height:145px; box-shadow: 0 8px 24px rgba(0,0,0,.10); }}
        .dark-card h3, .dark-card h4 {{ color:white; margin:0 0 .7rem; }}
        .green-card {{ background:{TEAL}; color:white; border-radius:14px; padding:1.5rem; min-height:145px; }}
        .blue-card {{ background:{BLUE}; color:white; border-radius:14px; padding:1.5rem; min-height:145px; }}
        .card-title {{ font-size:1.35rem; font-weight:800; margin-bottom:.5rem; }}
        .kpi-grid {{ display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1rem; margin: 1.2rem 0 1.4rem; }}
        .kpi {{ background:white; border:1px solid #e9ecef; border-radius:18px; padding:1.25rem; box-shadow:0 12px 30px rgba(18,30,46,.07); position:relative; overflow:hidden; }}
        .kpi::before {{ content:""; position:absolute; left:0; top:0; width:7px; height:100%; background:{PRIMARY}; }}
        .kpi .label {{ color:#6b7280; font-weight:700; font-size:.88rem; text-transform:uppercase; letter-spacing:.04em; }}
        .kpi .value {{ font-size:2.15rem; font-weight:850; color:{NAVY}; margin:.2rem 0; }}
        .kpi .delta {{ color:{PRIMARY}; font-weight:800; font-size:.9rem; }}
        .alert-green {{ display:flex; gap:1rem; align-items:flex-start; background:{LIGHT_GREEN}; color:#111827; border-radius:12px; padding:1.2rem 1.35rem; font-size:1.02rem; margin:1.25rem 0; }}
        .alert-blue {{ display:flex; gap:1rem; align-items:flex-start; background:#b7d9ff; color:#0b1324; border-radius:12px; padding:1.2rem 1.35rem; font-size:1.02rem; margin:1.25rem 0; }}
        .quote-line {{ border-left:4px solid {NAVY}; padding-left:1.4rem; margin:1.4rem 0; font-size:1.04rem; }}
        .app-table {{ width:100%; border-collapse:separate; border-spacing:0; overflow:hidden; border-radius:12px; border:1px solid #e5e7eb; background:#fff; }}
        .app-table th {{ text-align:left; padding:1rem; font-weight:800; background:#fff; border-bottom:1px solid #e5e7eb; }}
        .app-table td {{ padding:1rem; border-bottom:1px solid #f0f0f0; }}
        .app-table tr:nth-child(even) td {{ background:#f5f5f5; }}
        .app-table tr:last-child td {{ border-bottom:0; }}
        .secret-card {{ border-radius:18px; overflow:hidden; background:#fff; border:1px solid #e6e8ec; box-shadow:0 16px 38px rgba(18,30,46,.10); height:100%; }}
        .secret-img {{ height:170px; background-image:url('{candle}'); background-size:cover; background-position:center; }}
        .chef-band {{ background-image: linear-gradient(90deg, rgba(29,36,56,.88), rgba(29,36,56,.18)), url('{chef}'); background-size:cover; background-position:center; border-radius:22px; min-height:260px; padding:2rem; display:flex; align-items:flex-end; color:white; }}
        .badge {{ display:inline-block; border-radius:999px; padding:.35rem .68rem; font-size:.78rem; font-weight:800; }}
        .badge-green {{ background:#e8f7ef; color:{PRIMARY}; }}
        .badge-navy {{ background:{NAVY}; color:#fff; }}
        .badge-blue {{ background:#e8f2ff; color:{BLUE}; }}
        .timeline {{ position:relative; margin:2rem 0; }}
        .timeline-line {{ height:2px; background:#d6d8de; position:absolute; top:50%; left:2%; right:2%; }}
        .timeline-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; position:relative; }}
        .timeline-card {{ background:{NAVY}; color:#fff; padding:1rem; border-radius:10px; min-height:135px; box-shadow:0 10px 26px rgba(29,36,56,.14); }}
        .timeline-card:nth-child(2) {{ margin-top:6rem; background:{TEAL}; }}
        .timeline-card:nth-child(3) {{ background:{NAVY}; }}
        .timeline-card:nth-child(4) {{ margin-top:6rem; background:{NAVY}; }}
        .svg-wrap {{ background:white; border:1px solid #e6e8ec; border-radius:18px; padding:1rem; box-shadow:0 12px 30px rgba(18,30,46,.07); }}
        .stButton > button[kind="primary"] {{ background:{PRIMARY}; border-color:{PRIMARY}; border-radius:12px; font-weight:800; }}
        .stButton > button {{ border-radius:12px; font-weight:700; }}
        input, textarea, select {{ border-radius:10px !important; }}
        @media(max-width: 850px) {{
            .hero {{ grid-template-columns:1fr; }} .hero-img {{ min-height:300px; }} .hero-copy {{ padding:2rem; }}
            .kpi-grid {{ grid-template-columns:1fr 1fr; }} .timeline-grid {{ grid-template-columns:1fr; }} .timeline-card:nth-child(n) {{ margin-top:0; }}
        }}
        @media(max-width: 560px) {{ .kpi-grid {{ grid-template-columns:1fr; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def execute(sql: str, params: Iterable[Any] = ()) -> None:
    with closing(db()) as con:
        con.execute(sql, tuple(params))
        con.commit()


def fetchall(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with closing(db()) as con:
        return con.execute(sql, tuple(params)).fetchall()


def fetchone(sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with closing(db()) as con:
        return con.execute(sql, tuple(params)).fetchone()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
    except ValueError:
        return False
    calculated = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(calculated, expected)


def init_db() -> None:
    with closing(db()) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','manager','customer')),
                membership_status TEXT NOT NULL DEFAULT 'free',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                area TEXT NOT NULL,
                stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 3),
                taste TEXT NOT NULL,
                manager_id INTEGER,
                active INTEGER NOT NULL DEFAULT 1,
                avg_rating REAL NOT NULL DEFAULT 4.8,
                FOREIGN KEY(manager_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS availabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                service_date TEXT NOT NULL,
                service_time TEXT NOT NULL,
                seats INTEGER NOT NULL CHECK(seats IN (2,4)),
                price_per_person INTEGER NOT NULL,
                restaurant_fee INTEGER NOT NULL CHECK(restaurant_fee IN (30,50)),
                status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','booked','expired')),
                menu_title TEXT NOT NULL,
                experience TEXT NOT NULL,
                published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                availability_id INTEGER NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                guest_name TEXT NOT NULL,
                guests INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled','completed')),
                gross_value INTEGER NOT NULL,
                platform_fee INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(availability_id) REFERENCES availabilities(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL UNIQUE,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(booking_id) REFERENCES bookings(id)
            );
            CREATE INDEX IF NOT EXISTS idx_availabilities_status_date ON availabilities(status, service_date);
            CREATE INDEX IF NOT EXISTS idx_restaurants_city_taste ON restaurants(city, taste);
            CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
            """
        )
        con.commit()


def seed_db() -> None:
    if fetchone("SELECT id FROM users LIMIT 1"):
        return
    users = [
        ("Admin Secret Star", "admin@secretstar.local", "Admin123!", "admin", "premium"),
        ("Manager Milano", "manager@secretstar.local", "Manager123!", "manager", "premium"),
        ("Cliente Premium", "cliente@secretstar.local", "Cliente123!", "customer", "premium"),
    ]
    for name, email, password, role, membership in users:
        execute(
            "INSERT INTO users(name,email,password_hash,role,membership_status) VALUES(?,?,?,?,?)",
            (name, email, hash_password(password), role, membership),
        )
    manager = fetchone("SELECT id FROM users WHERE email=?", ("manager@secretstar.local",))["id"]
    restaurants = [
        ("Aurum Milano", "Milano", "Brera", 2, "Contemporaneo", manager, 4.9),
        ("Lago Segreto", "Como", "Lago", 1, "Lombardo", manager, 4.8),
        ("Nebbia d'Oro", "Bergamo", "Città Alta", 1, "Creativo", manager, 4.7),
        ("Franciacorta Atelier", "Brescia", "Franciacorta", 2, "Wine pairing", manager, 4.9),
        ("Scala Verde", "Milano", "Porta Nuova", 3, "Vegetale", manager, 5.0),
        ("Seta Notturna", "Milano", "Navigli", 1, "Fusion", manager, 4.6),
    ]
    for row in restaurants:
        execute("INSERT INTO restaurants(name,city,area,stars,taste,manager_id,avg_rating) VALUES(?,?,?,?,?,?,?)", row)
    today = date.today()
    restaurants_ids = [r["id"] for r in fetchall("SELECT id FROM restaurants")]
    menu_titles = ["Menu Degustazione Secret", "Percorso Signature", "Cena Stelle e Terroir", "Experience Limited Table"]
    tastes = ["tavolo intimo, menu completo e pairing opzionale", "esperienza premium last-minute con identità riservata"]
    for offset in range(0, 8):
        for i, rid in enumerate(restaurants_ids):
            seats = 2 if (i + offset) % 2 == 0 else 4
            price = [110, 125, 135, 150][(i + offset) % 4]
            fee = 30 if price < 135 else 50
            status = "available"
            execute(
                """INSERT INTO availabilities(restaurant_id,service_date,service_time,seats,price_per_person,restaurant_fee,status,menu_title,experience)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (rid, str(today + timedelta(days=offset)), "20:30", seats, price, fee, status, menu_titles[(i + offset) % 4], tastes[(i + offset) % 2]),
            )
    # Create a few historical confirmed bookings for dashboard economics.
    customer = fetchone("SELECT id FROM users WHERE email=?", ("cliente@secretstar.local",))["id"]
    past = fetchall("SELECT id,seats,price_per_person,restaurant_fee FROM availabilities ORDER BY id LIMIT 8")
    for a in past:
        execute("UPDATE availabilities SET status='booked' WHERE id=?", (a["id"],))
        execute(
            "INSERT OR IGNORE INTO bookings(availability_id,user_id,guest_name,guests,status,gross_value,platform_fee,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (a["id"], customer, "Cliente Premium", a["seats"], "completed", a["seats"] * a["price_per_person"], a["restaurant_fee"], str(datetime.now() - timedelta(days=8 - a["id"]))),
        )


def current_user() -> sqlite3.Row | None:
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    return fetchone("SELECT * FROM users WHERE id=?", (uid,))


def login_page() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-img"></div>
            <div class="hero-copy">
                <div class="hero-title">Secret Star Restaurant</div>
                <div class="hero-subtitle">Una piattaforma premium per valorizzare la capacità inutilizzata dei ristoranti stellati.</div>
                <div class="hero-quote">“Diamo nuova vita ai tavoli più esclusivi”</div>
                <div class="pill-row">
                    <span class="pill">Last-minute</span><span class="pill">Membership</span><span class="pill">Fine dining</span><span class="pill">Yield management</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("### Accesso piattaforma")
        with st.form("login"):
            email = st.text_input("Email", value="admin@secretstar.local")
            password = st.text_input("Password", value="Admin123!", type="password")
            submitted = st.form_submit_button("Entra", type="primary", use_container_width=True)
        if submitted:
            user = fetchone("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
            if user and verify_password(password, user["password_hash"]):
                st.session_state.user_id = user["id"]
                st.session_state.page = "Dashboard"
                st.rerun()
            st.error("Credenziali non valide.")
    with right:
        st.markdown(
            """
            <div class="panel">
                <h3>Credenziali demo</h3>
                <table class="app-table">
                    <tr><th>Ruolo</th><th>Email</th><th>Password</th></tr>
                    <tr><td>Admin</td><td>admin@secretstar.local</td><td>Admin123!</td></tr>
                    <tr><td>Manager</td><td>manager@secretstar.local</td><td>Manager123!</td></tr>
                    <tr><td>Cliente</td><td>cliente@secretstar.local</td><td>Cliente123!</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )


def sidebar(user: sqlite3.Row) -> str:
    st.sidebar.markdown(f"## ⭐ {APP_TITLE}")
    st.sidebar.markdown(f"**{html.escape(user['name'])}**  \n{html.escape(user['role']).title()} · {html.escape(user['membership_status']).title()}")
    st.sidebar.divider()
    pages = ["Dashboard", "Marketplace", "Prenotazioni", "Ristoranti", "Business Case", "Roadmap", "Amministrazione"]
    default = st.session_state.get("page", "Dashboard")
    page = st.sidebar.radio("Menu", pages, index=pages.index(default) if default in pages else 0, label_visibility="collapsed")
    st.session_state.page = page
    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    return page


def kpi_grid(items: list[tuple[str, str, str]]) -> None:
    html_items = "".join(
        f"<div class='kpi'><div class='label'>{html.escape(label)}</div><div class='value'>{html.escape(value)}</div><div class='delta'>{html.escape(delta)}</div></div>"
        for label, value, delta in items
    )
    st.markdown(f"<div class='kpi-grid'>{html_items}</div>", unsafe_allow_html=True)


def table_html(headers: list[str], rows: list[list[Any]], bold_cols: set[int] | None = None) -> str:
    bold_cols = bold_cols or set()
    head = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = ""
        for i, value in enumerate(row):
            text = html.escape(str(value))
            cells += f"<td>{'<b>' + text + '</b>' if i in bold_cols else text}</td>"
        body += f"<tr>{cells}</tr>"
    return f"<table class='app-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def line_svg(values: list[int], labels: list[str], title: str) -> str:
    width, height = 900, 360
    pad_l, pad_r, pad_t, pad_b = 58, 30, 35, 55
    min_v, max_v = min(values), max(values)
    span = max(max_v - min_v, 1)
    points = []
    for i, v in enumerate(values):
        x = pad_l + i * ((width - pad_l - pad_r) / (len(values) - 1))
        y = pad_t + (max_v - v) * ((height - pad_t - pad_b) / span)
        points.append((x, y, v))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
    area = f"{pad_l},{height-pad_b} " + polyline + f" {width-pad_r},{height-pad_b}"
    grid = "".join(f"<line x1='{pad_l}' x2='{width-pad_r}' y1='{pad_t+i*54}' y2='{pad_t+i*54}' stroke='#e6e8ec' stroke-dasharray='4 4'/>" for i in range(6))
    dots = "".join(
        f"<circle cx='{x:.1f}' cy='{y:.1f}' r='5' fill='{NAVY}'/><rect x='{x-16:.1f}' y='{y-30:.1f}' width='34' height='22' rx='8' fill='#f0f1f3'/><text x='{x+1:.1f}' y='{y-15:.1f}' text-anchor='middle' font-size='12' font-weight='700' fill='#111827'>{v}</text>"
        for x, y, v in points
    )
    xlabels = "".join(
        f"<text x='{x:.1f}' y='{height-22}' text-anchor='middle' font-size='12' fill='#202124'>{html.escape(labels[i])}</text>"
        for i, (x, _, _) in enumerate(points)
    )
    return f"""
    <div class='svg-wrap'>
    <svg viewBox='0 0 {width} {height}' width='100%' role='img' aria-label='{html.escape(title)}'>
        <text x='{pad_l}' y='22' font-size='18' font-weight='800' fill='{PRIMARY}'>{html.escape(title)}</text>
        {grid}
        <polygon points='{area}' fill='#eef0f3'/>
        <polyline points='{polyline}' fill='none' stroke='{NAVY}' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/>
        {dots}{xlabels}
        <text x='{width-96}' y='{pad_t+8}' font-size='12' font-weight='700' fill='{NAVY}'>Ristoranti attivi</text>
    </svg>
    </div>
    """


def bar_svg(labels: list[str], values: list[int], title: str) -> str:
    width, height = 900, 330
    max_v = max(values) or 1
    bars = []
    for i, (lab, val) in enumerate(zip(labels, values)):
        x = 75 + i * 220
        h = int((val / max_v) * 190)
        y = 255 - h
        bars.append(f"<rect x='{x}' y='{y}' width='120' height='{h}' rx='12' fill='{[NAVY, TEAL, BLUE][i % 3]}'/><text x='{x+60}' y='{y-12}' text-anchor='middle' font-size='18' font-weight='800' fill='{PRIMARY}'>{val:,}</text><text x='{x+60}' y='285' text-anchor='middle' font-size='14' font-weight='700' fill='#202124'>{html.escape(lab)}</text>")
    return f"<div class='svg-wrap'><svg viewBox='0 0 {width} {height}' width='100%'><text x='40' y='34' font-size='18' font-weight='800' fill='{PRIMARY}'>{html.escape(title)}</text>{''.join(bars)}</svg></div>"


def dashboard_page() -> None:
    bookings = fetchone("SELECT COUNT(*) c, COALESCE(SUM(gross_value),0) gbv, COALESCE(SUM(platform_fee),0) fees FROM bookings")
    avail = fetchone("SELECT COUNT(*) c FROM availabilities WHERE status='available'")
    rests = fetchone("SELECT COUNT(*) c FROM restaurants WHERE active=1")
    users = fetchone("SELECT COUNT(*) c FROM users")
    sub_revenue = users["c"] * 3.99 * 12
    kpi_grid([
        ("Prenotazioni", f"{bookings['c']}", "+ stesso giorno"),
        ("GBV gestito", f"€{bookings['gbv']:,.0f}".replace(",", "."), "tavolo + menu"),
        ("Fee piattaforma", f"€{bookings['fees']:,.0f}".replace(",", "."), "success fee"),
        ("Tavoli disponibili", str(avail["c"]), "inventory premium"),
    ])
    st.markdown("## Dashboard operativa")
    st.markdown("La piattaforma trasforma tavoli vuoti in ricavo incrementale: i ristoranti comunicano la disponibilità entro le 10:00, gli utenti premium prenotano esperienze last-minute e il nome resta riservato fino alla conferma.")
    c1, c2 = st.columns([1.1, .9], gap="large")
    with c1:
        st.markdown(bar_svg(["Low", "Base", "High"], [6400, 9600, 12800], "Prenotazioni annue in Lombardia"), unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"""
            <div class='dark-card'>
                <div class='card-title'>Run-rate Lombardia</div>
                <p>A regime, con 64 ristoranti attivi e scenario base:</p>
                <ul><li><b>9.600</b> prenotazioni annue</li><li><b>€518k–€710k</b> ricavi piattaforma</li><li><b>€2,1M–€5,8M</b> Gross Booking Value</li></ul>
            </div>
            <div style='height:1rem'></div>
            <div class='green-card'>
                <div class='card-title'>Subscription stimata demo</div>
                <p>Ricavi ricorrenti demo annui: <b>€{sub_revenue:,.0f}</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("### Capacità inutilizzata e qualità")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        st.markdown("""
        <div class='panel'>
            <h3>Costi fissi, capacità limitata</h3>
            <p>I ristoranti stellati operano con standard elevati e costi fissi importanti. Anche un singolo tavolo vuoto rappresenta mancato fatturato.</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class='panel' style='border-color:#1d7f64'>
            <h3>Monetizzare senza perdere esclusività</h3>
            <p>La disponibilità last-minute resta controllata e riservata: non è discount dining, è yield management applicato al fine dining.</p>
        </div>
        """, unsafe_allow_html=True)


def marketplace_page(user: sqlite3.Row) -> None:
    st.markdown("## Marketplace last-minute")
    st.markdown("Scegli taste, location ed esperienza. Il ristorante resta **Secret** fino alla prenotazione confermata.")
    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.selectbox("Location", ["Tutte", "Milano", "Como", "Bergamo", "Brescia"])
    with col2:
        seats = st.selectbox("Persone", ["Tutte", "2", "4"])
    with col3:
        taste = st.text_input("Ricerca taste", "")
    sql = """
    SELECT a.*, r.city, r.area, r.stars, r.taste, r.avg_rating
    FROM availabilities a JOIN restaurants r ON r.id=a.restaurant_id
    WHERE a.status='available' AND a.service_date>=?
    """
    params: list[Any] = [str(date.today())]
    if city != "Tutte":
        sql += " AND r.city=?"
        params.append(city)
    if seats != "Tutte":
        sql += " AND a.seats=?"
        params.append(int(seats))
    if taste.strip():
        sql += " AND lower(r.taste) LIKE ?"
        params.append(f"%{taste.lower()}%")
    sql += " ORDER BY a.service_date, a.price_per_person LIMIT 24"
    rows = fetchall(sql, params)
    if not rows:
        st.info("Nessun tavolo disponibile con questi filtri.")
        return
    cards = st.columns(3)
    for idx, a in enumerate(rows):
        with cards[idx % 3]:
            st.markdown(
                f"""
                <div class='secret-card'>
                    <div class='secret-img'></div>
                    <div style='padding:1.1rem'>
                        <span class='badge badge-navy'>Secret Restaurant #{a['restaurant_id']}</span>
                        <span class='badge badge-green'>{a['stars']}★</span>
                        <h3 style='font-size:1.25rem;margin:.8rem 0 .2rem'>Taste {html.escape(a['taste'])}</h3>
                        <p class='small-muted'>{html.escape(a['city'])} · {html.escape(a['area'])} · {a['service_date']} · {a['service_time']}</p>
                        <p>{html.escape(a['menu_title'])}<br><b>€{a['price_per_person']} pp</b> · {a['seats']} persone · rating {a['avg_rating']}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Prenota tavolo", key=f"book_{a['id']}", type="primary", use_container_width=True):
                if user["membership_status"] != "premium":
                    st.error("Serve una membership premium attiva per prenotare.")
                else:
                    gross = a["seats"] * a["price_per_person"]
                    try:
                        execute("UPDATE availabilities SET status='booked' WHERE id=? AND status='available'", (a["id"],))
                        execute(
                            "INSERT INTO bookings(availability_id,user_id,guest_name,guests,gross_value,platform_fee) VALUES(?,?,?,?,?,?)",
                            (a["id"], user["id"], user["name"], a["seats"], gross, a["restaurant_fee"]),
                        )
                        st.success("Prenotazione confermata. Ora il ristorante è visibile nella sezione Prenotazioni.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.warning("Questo tavolo è stato appena prenotato da un altro utente.")


def bookings_page(user: sqlite3.Row) -> None:
    st.markdown("## Prenotazioni")
    if user["role"] == "customer":
        params: list[Any] = [user["id"]]
        where = "WHERE b.user_id=?"
    else:
        params = []
        where = ""
    rows = fetchall(
        f"""
        SELECT b.*, a.service_date, a.service_time, a.price_per_person, r.name restaurant, r.city, r.area, r.stars
        FROM bookings b
        JOIN availabilities a ON a.id=b.availability_id
        JOIN restaurants r ON r.id=a.restaurant_id
        {where}
        ORDER BY b.created_at DESC
        """,
        params,
    )
    if not rows:
        st.info("Non ci sono prenotazioni.")
        return
    rows_html = [[r["id"], r["restaurant"], f"{r['city']} · {r['area']}", f"{r['service_date']} {r['service_time']}", r["guests"], f"€{r['gross_value']}", r["status"]] for r in rows]
    st.markdown(table_html(["ID", "Ristorante", "Location", "Servizio", "Pax", "GBV", "Stato"], rows_html, {1, 5}), unsafe_allow_html=True)
    st.markdown("### Lascia una review")
    completed = [r for r in rows if r["status"] in ("confirmed", "completed")]
    if completed:
        bid = st.selectbox("Prenotazione", [int(r["id"]) for r in completed])
        rating = st.slider("Rating", 1, 5, 5)
        comment = st.text_area("Commento", "Esperienza premium, servizio eccellente e ottima gestione last-minute.")
        if st.button("Salva review", type="primary"):
            try:
                execute("INSERT OR REPLACE INTO reviews(booking_id,rating,comment) VALUES(?,?,?)", (bid, rating, comment.strip()))
                st.success("Review salvata.")
            except sqlite3.Error as exc:
                st.error(f"Errore: {exc}")


def restaurants_page(user: sqlite3.Row) -> None:
    st.markdown("## Ristoranti stellati")
    st.markdown("Il network parte da Milano e cresce fino alla Lombardia premium: Lago di Como, Bergamo, Brescia e Franciacorta.")
    if user["role"] in ("admin", "manager"):
        with st.expander("Aggiungi ristorante"):
            with st.form("new_restaurant"):
                name = st.text_input("Nome ristorante")
                c1, c2, c3 = st.columns(3)
                with c1:
                    city = st.text_input("Città", "Milano")
                with c2:
                    area = st.text_input("Area", "Brera")
                with c3:
                    stars = st.selectbox("Stelle", [1, 2, 3])
                taste = st.text_input("Taste", "Contemporaneo")
                if st.form_submit_button("Crea", type="primary") and name.strip():
                    execute("INSERT INTO restaurants(name,city,area,stars,taste,manager_id,avg_rating) VALUES(?,?,?,?,?,?,?)", (name.strip(), city.strip(), area.strip(), stars, taste.strip(), user["id"], 4.8))
                    st.success("Ristorante creato.")
                    st.rerun()
    rows = fetchall("SELECT * FROM restaurants ORDER BY city, stars DESC")
    table = [[r["name"], r["city"], r["area"], f"{r['stars']}★", r["taste"], r["avg_rating"], "Attivo" if r["active"] else "Non attivo"] for r in rows]
    st.markdown(table_html(["Nome", "Città", "Area", "Stelle", "Taste", "Rating", "Stato"], table, {0, 3}), unsafe_allow_html=True)
    st.markdown("### Pubblica disponibilità entro le 10:00")
    if user["role"] in ("admin", "manager"):
        restaurants = fetchall("SELECT id,name FROM restaurants WHERE active=1 ORDER BY name")
        with st.form("new_availability"):
            rid = st.selectbox("Ristorante", restaurants, format_func=lambda r: r["name"])
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                service_date = st.date_input("Data", date.today())
            with c2:
                service_time = st.text_input("Ora", "20:30")
            with c3:
                seats = st.selectbox("Pax", [2, 4])
            with c4:
                price = st.number_input("Prezzo pp", 90, 300, 125)
            fee = st.selectbox("Fee ristorante", [30, 50])
            menu = st.text_input("Menu", "Menu Degustazione Secret")
            exp = st.text_area("Esperienza", "Pacchetto tavolo + menu a prezzo competitivo.")
            if st.form_submit_button("Pubblica tavolo", type="primary"):
                execute(
                    "INSERT INTO availabilities(restaurant_id,service_date,service_time,seats,price_per_person,restaurant_fee,menu_title,experience) VALUES(?,?,?,?,?,?,?,?)",
                    (rid["id"], str(service_date), service_time, seats, int(price), int(fee), menu, exp),
                )
                st.success("Disponibilità pubblicata.")
                st.rerun()
    else:
        st.info("Solo manager e admin possono pubblicare tavoli.")


def business_case_page() -> None:
    st.markdown("## Business case e modello ricavi")
    st.markdown("Il modello combina subscription utente e success fee dal ristorante, con monetizzazione della capacità inutilizzata e mantenimento del posizionamento premium.")
    c1, c2 = st.columns([1.2, .8], gap="large")
    with c1:
        st.markdown(table_html(["Variabile", "Ipotesi"], [
            ["Ristoranti nel pilot", "64"], ["Tavoli disponibili per ristorante", "1 al giorno"], ["Settimane operative", "50 all'anno"],
            ["Giorni vendibili a settimana", "2 / 3 / 4"], ["Persone per tavolo", "2 o 4"], ["Prezzo per persona", "negoziato con Ristorante"],
            ["Fee trattenuta al ristorante", "€30 o €50 per tavolo"], ["Subscription utente", "€3,99 al mese"],
        ], {0}), unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='dark-card'><div class='card-title'>Scenario Low</div><p>2 giorni a settimana</p></div><br>
        <div class='green-card'><div class='card-title'>Scenario Base</div><p>3 giorni a settimana</p></div><br>
        <div class='blue-card'><div class='card-title'>Scenario High</div><p>4 giorni a settimana</p></div>
        """, unsafe_allow_html=True)
    st.markdown("### Ricavi annui potenziali — Lombardia")
    st.markdown(table_html(["Scenario", "Fee €30 + subscription", "Fee €50 + subscription"], [
        ["Low", "€345.216", "€473.216"], ["Base", "€517.824", "€709.824"], ["High", "€690.432", "€946.432"],
    ], {0, 1, 2}), unsafe_allow_html=True)
    st.markdown("<div class='alert-green'>✓ <span>Il pilot lombardo può avvicinarsi a <b>€1M di ricavi annui</b> prima dello scale-up nazionale.</span></div>", unsafe_allow_html=True)
    st.markdown("### Upside Italia")
    st.markdown("<h1 style='text-align:center;color:#5bbda5'>394 × 3 × 50 = 59.100<br>prenotazioni/anno</h1>", unsafe_allow_html=True)
    c3, c4 = st.columns(2, gap="large")
    with c3:
        st.markdown(table_html(["Volumi e GBV — Italia", "Scenario base"], [["Prenotazioni annue", "59.100"], ["GTV minimo (2 pax × €110)", "€13,0M"], ["GTV massimo (4 pax × €150)", "€35,5M"]], {1}), unsafe_allow_html=True)
    with c4:
        st.markdown(table_html(["Voce", "Fee €30", "Fee €50"], [["Ricavi da fee ristorante", "€1,77M", "€2,96M"], ["Ricavi da subscription", "€1,42M", "€1,42M"], ["Totale ricavi", "€3,19M", "€4,37M"]], {0,1,2}), unsafe_allow_html=True)


def roadmap_page() -> None:
    st.markdown("## Implementazione graduale: da Milano alla Lombardia in 12 mesi")
    st.markdown("La piattaforma parte da Milano con 5 ristoranti selezionati e cresce con incremento medio del 26% mensile fino a circa 64 ristoranti attivi in Lombardia entro 12 mesi.")
    st.markdown("""
    <div class='timeline'>
        <div class='timeline-line'></div>
        <div class='timeline-grid'>
            <div class='timeline-card'><b>Mesi 1-3: Milano pilot</b><ul><li>5 ristoranti stellati selezionati</li><li>Onboarding e primi utenti premium</li><li>Validazione processo operativo</li></ul></div>
            <div class='timeline-card'><b>Mesi 4-6: Milano estesa</b><ul><li>Espansione network milanese</li><li>Attivazione domanda qualificata</li><li>Test pricing e conversione</li></ul></div>
            <div class='timeline-card'><b>Mesi 7-9: Lombardia premium</b><ul><li>Lago di Como, Bergamo, Brescia</li><li>Posizionamento esclusivo</li><li>Crescita liquidità marketplace</li></ul></div>
            <div class='timeline-card'><b>Mesi 10-12: Target Lombardia</b><ul><li>~64 ristoranti attivi</li><li>Preparazione scale-up Nord Italia</li></ul></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    values = [5, 6, 8, 10, 13, 16, 20, 25, 32, 40, 51, 64]
    labels = [f"Mese {i}" for i in range(1, 13)]
    st.markdown(line_svg(values, labels, "Crescita ristoranti attivi"), unsafe_allow_html=True)
    st.markdown("### Ricavi anno 1 con implementazione graduale")
    st.markdown(table_html(["Scenario", "Prenotazioni anno 1", "Ricavi fee €30", "Ricavi fee €50", "Ricavi subscription", "Totali €30", "Totali €50"], [
        ["Low, 2 giorni/settimana", "~2.406", "€72k", "€120k", "€58k", "€130k", "€178k"],
        ["Base, 3 giorni/settimana", "~3.609", "€108k", "€180k", "€86k", "€195k", "€267k"],
        ["High, 4 giorni/settimana", "~4.812", "€144k", "€241k", "€115k", "€260k", "€356k"],
    ], {0}), unsafe_allow_html=True)
    st.markdown("<div class='alert-green'>✓ <span>A regime, con 64 ristoranti attivi in Lombardia, lo scenario base genera <b>9.600 prenotazioni annue</b>, <b>€2,1M–€5,8M</b> di GBV e <b>€518k–€710k</b> di ricavi annui piattaforma.</span></div>", unsafe_allow_html=True)


def admin_page(user: sqlite3.Row) -> None:
    st.markdown("## Amministrazione")
    if user["role"] != "admin":
        st.warning("Pagina disponibile solo per admin.")
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Reset database demo", use_container_width=True):
            if DB_PATH.exists():
                DB_PATH.unlink()
            init_db(); seed_db(); st.success("Database ricreato."); st.rerun()
    with c2:
        if st.button("Attiva membership a tutti", use_container_width=True):
            execute("UPDATE users SET membership_status='premium'")
            st.success("Membership aggiornate.")
    with c3:
        if st.button("Scadenza tavoli passati", use_container_width=True):
            execute("UPDATE availabilities SET status='expired' WHERE service_date<? AND status='available'", (str(date.today()),))
            st.success("Tavoli aggiornati.")
    users = fetchall("SELECT id,name,email,role,membership_status,created_at FROM users ORDER BY id")
    st.markdown("### Utenti")
    st.markdown(table_html(["ID", "Nome", "Email", "Ruolo", "Membership", "Creato"], [[u["id"], u["name"], u["email"], u["role"], u["membership_status"], u["created_at"]] for u in users], {1,3}), unsafe_allow_html=True)


def final_story() -> None:
    st.markdown("## Da tavoli vuoti a marketplace premium del fine dining")
    st.markdown("""
    <div class='chef-band'>
        <div>
            <h2 style='color:white'>Una nuova infrastruttura digitale per monetizzare l'invenduto premium</h2>
            <p style='font-size:1.15rem;max-width:720px'>Dal pilot lombardo al Nord Italia, fino all'espansione nazionale e alle città europee: Parigi, Londra, Barcellona, Zurigo.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main() -> None:
    init_db()
    seed_db()
    inject_css()
    user = current_user()
    if not user:
        login_page()
        return
    page = sidebar(user)
    if page == "Dashboard":
        dashboard_page()
    elif page == "Marketplace":
        marketplace_page(user)
    elif page == "Prenotazioni":
        bookings_page(user)
    elif page == "Ristoranti":
        restaurants_page(user)
    elif page == "Business Case":
        business_case_page()
    elif page == "Roadmap":
        roadmap_page()
    elif page == "Amministrazione":
        admin_page(user)
    final_story()


if __name__ == "__main__":
    main()
