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
PRIMARY = "#24a56a"
MINT = "#77d9bd"
NAVY = "#0f1724"
TEAL = "#197a5b"
BLUE = "#0b4f91"
LIGHT_GREEN = "#173c2b"
GOLD = "#d8b45f"
INK = "#050608"
CARD = "#101522"
CARD_2 = "#151b2a"

st.set_page_config(page_title=APP_TITLE, page_icon="⭐", layout="wide", initial_sidebar_state="collapsed")


def image_uri(name: str) -> str:
    path = ASSET_DIR / name
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("utf-8")


def restaurant_image_uri(restaurant_id: int | str) -> str:
    try:
        idx = ((int(restaurant_id) - 1) % 8) + 1
    except (TypeError, ValueError):
        idx = 1
    return image_uri(f"restaurant_{idx}.png")


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

        /* Elegant black visual system */
        html, body, [class*="css"] {{ font-family: Inter, Arial, sans-serif; }}
        .stApp {{ background: radial-gradient(circle at 20% 0%, rgba(36,165,106,.16), transparent 34%), linear-gradient(180deg, #050608 0%, #0b0e14 50%, #050608 100%); color: #f7f5ef; }}
        header[data-testid="stHeader"] {{ background: rgba(5,6,8,.72); backdrop-filter: blur(12px); }}
        .block-container {{ max-width: 1400px; padding-top: 1rem; padding-left: clamp(1rem,3vw,3rem); padding-right: clamp(1rem,3vw,3rem); }}
        h1, h2, h3 {{ color: #f7f5ef; }}
        .stMarkdown p, .stCaption, label, .small-muted {{ color: rgba(247,245,239,.76) !important; }}
        div[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #050608 0%, #0e1420 100%) !important; border-right: 1px solid rgba(216,180,95,.18); }}
        div[data-testid="stSidebar"] * {{ color: #f7f5ef !important; -webkit-text-fill-color: #f7f5ef !important; }}
        div[data-testid="stSidebar"] .stButton > button {{ background: rgba(216,180,95,.16) !important; color:#fff4cf !important; -webkit-text-fill-color:#fff4cf !important; border:1px solid rgba(216,180,95,.38) !important; }}
        div[data-testid="stSidebar"] .stButton > button:hover {{ background: rgba(36,165,106,.32) !important; border-color: rgba(119,217,189,.46) !important; }}
        div[data-testid="stSidebar"] .stRadio label {{ border-radius: 14px; padding: .45rem .6rem; }}
        .hero {{ background: #080a0f; border: 1px solid rgba(216,180,95,.25); box-shadow: 0 36px 100px rgba(0,0,0,.55); grid-template-columns: minmax(420px, 48%) 1fr; }}
        .hero-img {{ min-height: 600px; background-position: center; filter: saturate(.95) contrast(1.05); }}
        .hero-copy {{ background: linear-gradient(135deg, rgba(5,6,8,.96), rgba(15,23,36,.91)); position: relative; }}
        .hero-copy:before {{ content:""; position:absolute; inset: 1rem; border: 1px solid rgba(216,180,95,.18); border-radius: 22px; pointer-events:none; }}
        .hero-title {{ color: #f7f5ef; text-shadow: 0 8px 34px rgba(0,0,0,.45); }}
        .hero-subtitle {{ color: rgba(247,245,239,.82); }}
        .hero-quote {{ color: {GOLD}; }}
        .pill {{ background: rgba(216,180,95,.10); color: #f4d98f; border-color: rgba(216,180,95,.30); }}
        .panel, .kpi, .secret-card, .svg-wrap {{ background: linear-gradient(180deg, rgba(21,27,42,.96), rgba(12,16,25,.96)); border: 1px solid rgba(216,180,95,.18); box-shadow: 0 26px 55px rgba(0,0,0,.35); color: #f7f5ef; }}
        .panel h3, .panel h4 {{ color: #f7f5ef; }}
        .kpi::before {{ background: linear-gradient(180deg, {GOLD}, {PRIMARY}); }}
        .kpi .value {{ color: #f7f5ef; }}
        .kpi .label {{ color: rgba(247,245,239,.62); }}
        .kpi .delta {{ color: #f4d98f; }}
        .dark-card {{ background: linear-gradient(135deg, #111827, #07090e); border: 1px solid rgba(216,180,95,.18); }}
        .green-card {{ background: linear-gradient(135deg, #0f513c, #0a2219); border: 1px solid rgba(119,217,189,.26); }}
        .blue-card {{ background: linear-gradient(135deg, #0b4f91, #071629); border: 1px solid rgba(133,183,255,.25); }}
        .app-table {{ background: rgba(15,21,33,.95); border-color: rgba(216,180,95,.15); color: #f7f5ef; }}
        .app-table th {{ background: rgba(216,180,95,.07); color: #fff4cf; border-bottom-color: rgba(216,180,95,.18); }}
        .app-table td {{ border-bottom-color: rgba(255,255,255,.07); color: rgba(247,245,239,.88); }}
        .app-table tr:nth-child(even) td {{ background: rgba(255,255,255,.035); }}
        .alert-green {{ background: rgba(36,165,106,.16); border: 1px solid rgba(119,217,189,.25); color: #eafff6; }}
        .alert-blue {{ background: rgba(70,140,220,.17); border: 1px solid rgba(115,180,255,.24); color: #edf6ff; }}
        .quote-line {{ border-left-color: {GOLD}; color: rgba(247,245,239,.84); }}
        .secret-card {{ transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease; overflow:hidden; }}
        .secret-card:hover {{ transform: translateY(-4px); border-color: rgba(216,180,95,.45); box-shadow: 0 30px 80px rgba(0,0,0,.48); }}
        .secret-img {{ height: 235px; background-size: cover; background-position: center; position: relative; }}
        .secret-img:after {{ content:""; position:absolute; inset:0; background: linear-gradient(180deg, rgba(0,0,0,.08), rgba(0,0,0,.72)); }}
        .restaurant-name {{ color:#f7f5ef; font-size:1.15rem; font-weight:850; margin:.75rem 0 .2rem; }}
        .card-body-dark {{ padding:1.15rem; }}
        .badge-green {{ background: rgba(36,165,106,.18); color:#98f2ce; border:1px solid rgba(119,217,189,.20); }}
        .badge-navy {{ background: rgba(216,180,95,.13); color:#ffe5a3; border:1px solid rgba(216,180,95,.25); }}
        .badge-blue {{ background: rgba(11,79,145,.35); color:#c7defc; border:1px solid rgba(133,183,255,.20); }}
        .chef-band {{ border: 1px solid rgba(216,180,95,.20); box-shadow: 0 26px 60px rgba(0,0,0,.40); }}
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {{ background: rgba(255,255,255,.06) !important; color:#f7f5ef !important; border: 1px solid rgba(216,180,95,.20) !important; }}
        .stSelectbox div[data-baseweb="select"] > div {{ background: #ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; border-color: rgba(216,180,95,.45) !important; }}
        .stSelectbox div[data-baseweb="select"] span, .stSelectbox div[data-baseweb="select"] input, .stSelectbox div[data-baseweb="select"] [role="button"] {{ color:#000000 !important; -webkit-text-fill-color:#000000 !important; }}
        div[data-baseweb="popover"], div[data-baseweb="popover"] * {{ background:#ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; }}
        ul[role="listbox"], ul[role="listbox"] li, ul[role="listbox"] div {{ background:#ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; }}
        .stButton > button[kind="primary"] {{ background: linear-gradient(135deg, {PRIMARY}, #0b6a48); border-color: rgba(119,217,189,.35); color:white; }}
        .stButton > button {{ background: rgba(216,180,95,.08); color:#fff4cf; border:1px solid rgba(216,180,95,.25); }}
        /* Readability fixes for light popovers, menus and form fields */
        section[data-testid="stSidebar"], div[data-testid="stSidebar"] { background: linear-gradient(180deg, #050608 0%, #0e1420 100%) !important; }
        section[data-testid="stSidebar"] *, div[data-testid="stSidebar"] * { color:#f7f5ef !important; -webkit-text-fill-color:#f7f5ef !important; opacity:1 !important; }
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input,
        input, textarea { background:#ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; caret-color:#000000 !important; border-color:rgba(216,180,95,.45) !important; }
        .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div { background:#ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; }
        .stSelectbox div[data-baseweb="select"] *, .stMultiSelect div[data-baseweb="select"] * { color:#000000 !important; -webkit-text-fill-color:#000000 !important; }
        div[data-baseweb="popover"], div[data-baseweb="popover"] *, ul[role="listbox"], ul[role="listbox"] *, [role="option"], [role="option"] * { background:#ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; }
        div[data-testid="stSidebar"] .stButton > button { background: rgba(216,180,95,.16) !important; color:#fff4cf !important; -webkit-text-fill-color:#fff4cf !important; border:1px solid rgba(216,180,95,.38) !important; }
        .stButton > button { min-height:3.2rem; color:#fff4cf !important; -webkit-text-fill-color:#fff4cf !important; }
        

        .mode-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1rem; margin:1.25rem 0 1.5rem; }}
        .mode-card {{ background:linear-gradient(180deg, rgba(21,27,42,.96), rgba(8,10,15,.96)); border:1px solid rgba(216,180,95,.22); border-radius:18px; padding:1rem; min-height:118px; box-shadow:0 18px 46px rgba(0,0,0,.35); }}
        .mode-card h4 {{ margin:0 0 .4rem; color:#fff4cf; font-size:1.03rem; }}
        .mode-card p {{ margin:0; color:rgba(247,245,239,.72); font-size:.9rem; line-height:1.35; }}
        .mode-emoji {{ font-size:1.5rem; margin-bottom:.45rem; }}
        @media(max-width: 900px) {{ .mode-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
        @media(max-width: 560px) {{ .mode-grid {{ grid-template-columns:1fr; }} }}
        .mobile-only {{ display:none; }}
        @media(max-width: 900px) {{
            .hero {{ grid-template-columns:1fr; border-radius: 22px; }}
            .hero-img {{ min-height: 360px; }}
            .hero-copy {{ padding: 2rem 1.4rem; }}
            .hero-copy:before {{ inset:.6rem; border-radius: 18px; }}
            .secret-img {{ height: 220px; }}
            .desktop-only {{ display:none; }} .mobile-only {{ display:block; }}
        }}
        @media(max-width: 640px) {{
            .block-container {{ padding-left: .9rem; padding-right: .9rem; }}
            .hero-img {{ min-height: 300px; }}
            .hero-title {{ font-size: 2.35rem; }}
            .hero-subtitle {{ font-size: 1rem; }}
            .hero-quote {{ font-size: 1.22rem; }}
            .secret-card {{ border-radius: 16px; }}
            .secret-img {{ height: 200px; }}
            .app-table th, .app-table td {{ padding: .7rem; font-size: .86rem; }}
        }}

        /* Marketplace premium and interactive business case */
        .market-hero {{
            border-radius: 30px;
            padding: clamp(1.2rem, 3vw, 2.7rem);
            background:
                linear-gradient(90deg, rgba(3,5,7,.98) 0%, rgba(3,5,7,.94) 38%, rgba(3,5,7,.70) 63%, rgba(3,5,7,.48) 100%),
                linear-gradient(180deg, rgba(0,0,0,.50), rgba(0,0,0,.72)),
                url('{candle}');
            background-size: cover;
            background-position: center right;
            border: 1px solid rgba(216,180,95,.32);
            box-shadow: 0 34px 100px rgba(0,0,0,.58);
            margin-bottom: 1.3rem;
            overflow:hidden;
            position:relative;
            min-height: 430px;
            display:flex;
            align-items:flex-end;
        }}
        .market-hero:before {{
            content:"";
            position:absolute;
            inset:0;
            background: radial-gradient(circle at 86% 20%, rgba(216,180,95,.18), transparent 28%);
            pointer-events:none;
        }}
        .market-hero:after {{
            content:"";
            position:absolute;
            left:0; top:0; bottom:0;
            width:58%;
            background: linear-gradient(90deg, rgba(0,0,0,.72), rgba(0,0,0,.18), transparent);
            pointer-events:none;
        }}
        .market-hero > * {{ position:relative; z-index:2; }}
        .market-content {{
            width:min(920px, 100%);
            background:
                linear-gradient(135deg, rgba(5,7,10,.96), rgba(8,13,20,.90)),
                radial-gradient(circle at 12% 0%, rgba(216,180,95,.14), transparent 34%);
            border: 1px solid rgba(216,180,95,.38);
            border-radius: 28px;
            padding: clamp(1.15rem, 2.6vw, 1.95rem);
            box-shadow: 0 30px 90px rgba(0,0,0,.58), inset 0 1px 0 rgba(255,255,255,.05);
            backdrop-filter: blur(16px);
        }}
        .market-eyebrow {{ color:#f4d98f; text-transform:uppercase; letter-spacing:.18em; font-size:.78rem; font-weight:950; text-shadow:0 2px 12px rgba(0,0,0,.8); }}
        .market-title {{ color:#fff; font-size: clamp(2.25rem, 4.7vw, 4.65rem); line-height:.96; font-weight:950; letter-spacing:-.065em; margin:.48rem 0 .85rem; max-width:860px; text-shadow: 0 8px 34px rgba(0,0,0,.78); }}
        .market-sub {{ color:rgba(247,245,239,.95); font-size:1.08rem; line-height:1.62; max-width:760px; text-shadow:0 3px 20px rgba(0,0,0,.85); }}
        .market-line {{ display:inline-block; margin-top:.8rem; padding:.72rem .95rem; color:#fff7d9; font-weight:850; letter-spacing:-.01em; background:rgba(216,180,95,.12); border:1px solid rgba(216,180,95,.32); border-radius:999px; box-shadow: inset 0 1px 0 rgba(255,255,255,.05); }}
        .market-quick {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.8rem; margin-top:1.25rem; }}
        .quick-card {{ background:rgba(0,0,0,.72); border:1px solid rgba(216,180,95,.35); border-radius:18px; padding:1rem; backdrop-filter: blur(10px); box-shadow: inset 0 1px 0 rgba(255,255,255,.04); }}
        .quick-card b {{ display:block; color:#fff; font-size:1.25rem; }}
        .quick-card span {{ color:rgba(247,245,239,.66); font-size:.86rem; }}
        .market-card {{ display:grid; grid-template-columns: 42% 58%; min-height: 300px; border-radius: 24px; overflow:hidden; background:linear-gradient(180deg, rgba(21,27,42,.98), rgba(8,10,15,.98)); border:1px solid rgba(216,180,95,.22); box-shadow: 0 26px 70px rgba(0,0,0,.42); margin-bottom:1.1rem; }}
        .market-img {{ min-height:300px; background-size:cover; background-position:center; position:relative; }}
        .market-img:after {{ content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(0,0,0,.05), rgba(0,0,0,.76)); }}
        .market-img-label {{ position:absolute; left:1rem; right:1rem; bottom:1rem; z-index:1; display:flex; flex-wrap:wrap; gap:.45rem; }}
        .market-body {{ padding:1.35rem; display:flex; flex-direction:column; justify-content:space-between; }}
        .market-row {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap; }}
        .market-name {{ color:#fff; font-size:1.45rem; font-weight:900; letter-spacing:-.025em; margin:.55rem 0 .2rem; }}
        .market-meta {{ color:rgba(247,245,239,.68); font-weight:600; }}
        .market-price {{ color:#f4d98f; font-size:1.55rem; font-weight:950; }}
        .market-list {{ display:grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap:.5rem; margin:.9rem 0; }}
        .market-list div {{ background:rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.075); border-radius:12px; padding:.65rem .75rem; color:rgba(247,245,239,.82); }}
        .progress-shell {{ width:100%; height:12px; background:rgba(255,255,255,.08); border-radius:99px; overflow:hidden; border:1px solid rgba(216,180,95,.12); }}
        .progress-fill {{ height:100%; background:linear-gradient(90deg, #24a56a, #d8b45f); border-radius:99px; }}
        .calc-hero {{ border-radius:24px; padding:1.5rem; background:linear-gradient(135deg, rgba(36,165,106,.16), rgba(216,180,95,.10)); border:1px solid rgba(216,180,95,.22); margin:1rem 0; }}
        .calc-result {{ border-radius:22px; padding:1.2rem; background:linear-gradient(180deg, rgba(216,180,95,.13), rgba(36,165,106,.10)); border:1px solid rgba(216,180,95,.25); }}
        .big-number {{ color:#f4d98f; font-size:clamp(2rem,4vw,4.6rem); line-height:1; font-weight:950; letter-spacing:-.055em; }}
        .sensitivity-grid {{ display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap:1rem; }}
        @media(max-width: 900px) {{ .market-quick {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .market-card {{ grid-template-columns:1fr; }} .market-img {{ min-height:230px; }} .market-list {{ grid-template-columns:1fr; }} .sensitivity-grid {{ grid-template-columns:1fr; }} }}
        .reveal-box {{ background: linear-gradient(135deg, rgba(216,180,95,.18), rgba(36,165,106,.12)); border:1px solid rgba(216,180,95,.32); border-radius:18px; padding:1rem; margin:.8rem 0; color:#fff; }}
        .reveal-title {{ color:#f4d98f; font-weight:950; font-size:1.25rem; margin-bottom:.25rem; }}
        .warning-box {{ background: rgba(180,50,50,.16); border:1px solid rgba(255,120,120,.28); border-radius:16px; padding:1rem; color:#ffecec; margin:.8rem 0; }}
        .market-img:after {{ background:linear-gradient(180deg, rgba(0,0,0,.18), rgba(0,0,0,.88)); }}
        @media(max-width: 560px) {{
            .market-quick {{ grid-template-columns:1fr; gap:.65rem; }}
            .market-title {{ font-size:2.12rem; line-height:1; letter-spacing:-.045em; }}
            .market-sub {{ font-size:.98rem; line-height:1.52; }}
            .market-line {{ border-radius:16px; font-size:.92rem; line-height:1.35; }}
            .market-hero {{ border-radius:20px; padding:1rem; min-height:560px; align-items:flex-end; background-position:64% center; }}
            .market-content {{ border-radius:18px; padding:1rem; background:rgba(3,5,7,.91); }}
            .quick-card {{ padding:.85rem; }}
            .market-card {{ border-radius:18px; }}
            .market-body {{ padding:1rem; }}
            .market-name {{ font-size:1.2rem; }}
            .market-price {{ font-size:1.28rem; }}
        }}
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


def cancellation_count(user_id: int) -> int:
    row = fetchone("SELECT COUNT(*) c FROM bookings WHERE user_id=? AND status='cancelled'", (user_id,))
    return int(row["c"] if row else 0)


def create_booking_if_available(availability_id: int, user_id: int, guest_name: str, guests: int, gross_value: float, platform_fee: float) -> None:
    with closing(db()) as con:
        cur = con.execute(
            "UPDATE availabilities SET status='booked' WHERE id=? AND status='available'",
            (availability_id,),
        )
        if cur.rowcount != 1:
            raise sqlite3.IntegrityError("availability_not_available")
        con.execute(
            "INSERT INTO bookings(availability_id,user_id,guest_name,guests,gross_value,platform_fee) VALUES(?,?,?,?,?,?)",
            (availability_id, user_id, guest_name, guests, gross_value, platform_fee),
        )
        con.commit()


def cancel_booking(booking_id: int, user_id: int) -> bool:
    with closing(db()) as con:
        row = con.execute(
            """
            SELECT b.id, b.status, b.availability_id, a.service_date
            FROM bookings b JOIN availabilities a ON a.id=b.availability_id
            WHERE b.id=? AND b.user_id=?
            """,
            (booking_id, user_id),
        ).fetchone()
        if not row or row["status"] != "confirmed" or row["service_date"] < str(date.today()):
            return False
        con.execute("UPDATE bookings SET status='cancelled' WHERE id=? AND user_id=?", (booking_id, user_id))
        con.execute("UPDATE availabilities SET status='available' WHERE id=?", (row["availability_id"],))
        con.commit()
        return True


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
    pages = [
        ("Dashboard", "📊", "KPI, ricavi e andamento operativo."),
        ("Marketplace", "🍽️", "Esperienze disponibili e prenotazione tavoli."),
        ("Prenotazioni", "📅", "Gestione prenotazioni e stati."),
        ("Ristoranti", "⭐", "Anagrafica ristoranti e disponibilità."),
        ("Business Case", "📈", "Simulator, scenari e unit economics."),
        ("Roadmap", "🗺️", "Piano di crescita e milestone."),
        ("Amministrazione", "⚙️", "Operazioni admin e manutenzione dati."),
    ]
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
    st.markdown("### Accesso piattaforma")
    email = st.text_input("Email", value="admin@secretstar.local")
    st.markdown("### Modalità di visualizzazione")
    st.caption("Seleziona una sezione: i box qui sotto sono gli unici comandi di navigazione nella schermata iniziale.")

    cols = st.columns(4)
    for i, (page, emoji, desc) in enumerate(pages):
        with cols[i % 4]:
            st.markdown(f"<div class='small-muted'>{html.escape(desc)}</div>", unsafe_allow_html=True)
            if st.button(f"{emoji} {page}", key=f"enter_{page}", use_container_width=True):
                user = fetchone("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.page = page
                    st.rerun()
                st.error("Email non valida.")

    st.markdown(
        """
        <div class="panel">
            <h3>Profili demo</h3>
            <table class="app-table">
                <tr><th>Ruolo</th><th>Email</th></tr>
                <tr><td>Admin</td><td>admin@secretstar.local</td></tr>
                <tr><td>Manager</td><td>manager@secretstar.local</td></tr>
                <tr><td>Cliente</td><td>cliente@secretstar.local</td></tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

def sidebar(user: sqlite3.Row) -> str:
    """Sidebar ridotta: niente box/menu di modalità, perché la navigazione avviene dai box principali."""
    st.sidebar.markdown(f"## ⭐ {APP_TITLE}")
    st.sidebar.markdown(f"**{html.escape(user['name'])}**  \n{html.escape(user['role']).title()} · {html.escape(user['membership_status']).title()}")
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    return st.session_state.get("page", "Dashboard")

def top_navigation() -> None:
    """Navigazione principale nel corpo pagina: niente menu laterali o menu a tendina."""
    pages = [
        ("Dashboard", "📊"),
        ("Marketplace", "🍽️"),
        ("Prenotazioni", "📅"),
        ("Ristoranti", "⭐"),
        ("Business Case", "📈"),
        ("Roadmap", "🗺️"),
        ("Amministrazione", "⚙️"),
    ]
    cols = st.columns(4)
    current = st.session_state.get("page", "Dashboard")
    for i, (page, emoji) in enumerate(pages):
        with cols[i % 4]:
            label = f"{emoji} {page}" if page != current else f"● {emoji} {page}"
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.rerun()
    st.divider()


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



def eur(value: float, compact: bool = False) -> str:
    value = float(value or 0)
    if compact:
        abs_v = abs(value)
        if abs_v >= 1_000_000:
            return (f"€{value/1_000_000:.2f}M").replace('.', ',')
        if abs_v >= 1_000:
            return (f"€{value/1_000:.0f}k").replace('.', ',')
    return "€" + f"{value:,.0f}".replace(',', '.')


def int_it(value: float) -> str:
    return f"{int(round(value)):,.0f}".replace(',', '.')

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
    today = date.today()
    total_available = fetchone("SELECT COUNT(*) c FROM availabilities WHERE status='available' AND service_date>=?", (str(today),))["c"]
    avg_price = fetchone("SELECT COALESCE(AVG(price_per_person),0) v FROM availabilities WHERE status='available' AND service_date>=?", (str(today),))["v"]
    cities_count = fetchone("""
        SELECT COUNT(DISTINCT r.city) c
        FROM availabilities a JOIN restaurants r ON r.id=a.restaurant_id
        WHERE a.status='available' AND a.service_date>=?
    """, (str(today),))["c"]
    next_date = fetchone("SELECT MIN(service_date) d FROM availabilities WHERE status='available' AND service_date>=?", (str(today),))["d"] or str(today)
    user_cancellations = cancellation_count(int(user["id"]))
    blocked = user_cancellations >= 2

    st.markdown(
        f"""
        <div class='market-hero'>
            <div class='market-content'>
                <div class='market-eyebrow'>SECRET TABLES · SAME-DAY · FINE DINING</div>
                <div class='market-title'>Tonight’s most exclusive tables, quietly unlocked.</div>
                <div class='market-sub'>Esperienze stellate disponibili oggi. Accesso riservato, conferma immediata, ristorante secret fino al primo click.</div>
                <div class='market-line'>Hai 60 secondi per trasformare una disponibilità rara nel tuo tavolo di stasera.</div>
                <div class='market-quick'>
                    <div class='quick-card'><b>{total_available}</b><span>Tavoli premium disponibili</span></div>
                    <div class='quick-card'><b>{cities_count}</b><span>Location attive</span></div>
                    <div class='quick-card'><b>{eur(avg_price)}</b><span>Prezzo medio per persona</span></div>
                    <div class='quick-card'><b>{html.escape(str(next_date))}</b><span>Prima disponibilità</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if blocked:
        st.markdown(
            """
            <div class='warning-box'>
                <b>Prenotazioni bloccate.</b><br>
                Questo account ha già raggiunto 2 cancellazioni. Per preservare la qualità della community premium non è possibile effettuare nuove prenotazioni.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif user_cancellations == 1:
        st.warning("Hai già 1 cancellazione registrata. Alla seconda cancellazione il sistema bloccherà nuove prenotazioni.")

    with st.container():
        f1, f2, f3, f4 = st.columns([1, 1, 1, 1.2])
        with f1:
            city = st.selectbox("Location", ["Tutte", "Milano", "Como", "Bergamo", "Brescia"])
        with f2:
            guests_requested = st.selectbox("Persone", [1, 2, 3, 4], index=1)
        with f3:
            max_price = st.slider("Budget max per persona", 90, 300, 180, 5)
        with f4:
            taste = st.text_input("Ricerca", placeholder="città, area, menu o stile")

    sql = """
    SELECT a.*, r.name, r.city, r.area, r.stars, r.taste, r.avg_rating
    FROM availabilities a JOIN restaurants r ON r.id=a.restaurant_id
    WHERE a.status='available' AND a.service_date>=? AND a.price_per_person<=? AND a.seats>=?
    """
    params: list[Any] = [str(today), int(max_price), int(guests_requested)]
    if city != "Tutte":
        sql += " AND r.city=?"
        params.append(city)
    if taste.strip():
        sql += " AND (lower(r.taste) LIKE ? OR lower(r.area) LIKE ? OR lower(a.menu_title) LIKE ? OR lower(r.city) LIKE ?)"
        q = f"%{taste.lower()}%"
        params.extend([q, q, q, q])
    sql += " ORDER BY a.service_date, a.price_per_person, r.stars DESC LIMIT 24"
    rows = fetchall(sql, params)

    st.markdown("### Esperienze selezionate")
    if not rows:
        st.info("Nessun tavolo disponibile con questi filtri. Prova ad ampliare budget, location o numero di persone.")
        return

    now_ts = datetime.utcnow().timestamp()
    pending = st.session_state.get("pending_booking")
    if pending and now_ts > float(pending.get("expires_at", 0)):
        st.session_state.pop("pending_booking", None)
        pending = None
        st.warning("Il tempo di conferma è scaduto. Puoi selezionare di nuovo un tavolo se è ancora disponibile.")

    for idx, a in enumerate(rows):
        restaurant_code = f"SSR-{int(a['restaurant_id']):03d}"
        img = restaurant_image_uri(a['restaurant_id'])
        gross = int(guests_requested) * float(a["price_per_person"])
        pending_for_this = bool(pending and int(pending.get("availability_id", -1)) == int(a["id"]))
        display_name = html.escape(a["name"] if pending_for_this else restaurant_code)
        title_suffix = "Nome reale rivelato" if pending_for_this else "Esperienza riservata"
        st.markdown(
            f"""
            <div class='market-card'>
                <div class='market-img' style="background-image:url('{img}')">
                    <div class='market-img-label'>
                        <span class='badge badge-navy'>{'Ristorante rivelato' if pending_for_this else 'Secret fino alla prenotazione'}</span>
                        <span class='badge badge-green'>{a['stars']}★ Michelin</span>
                    </div>
                </div>
                <div class='market-body'>
                    <div>
                        <div class='market-row'>
                            <span class='badge badge-blue'>{html.escape(a['city'])} · {html.escape(a['area'])}</span>
                            <span class='market-price'>€{a['price_per_person']} pp</span>
                        </div>
                        <div class='market-name'>{display_name} · {title_suffix}</div>
                        <div class='market-meta'>{html.escape(a['service_date'])} · {html.escape(a['service_time'])} · prenoti {guests_requested} persone · tavolo fino a {a['seats']} · rating {a['avg_rating']}</div>
                        <div class='market-list'>
                            <div>🍽️ {html.escape(a['menu_title'])}</div>
                            <div>✨ Accesso riservato</div>
                            <div>📍 Location premium selezionata</div>
                            <div>🔒 Conferma finale entro 60 secondi</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b1, b2, b3 = st.columns([1.25, .9, 1])
        with b1:
            st.caption(f"Esperienza: {a['experience']}")
        with b2:
            if user["role"] == "customer":
                st.caption(f"Totale esperienza: {eur(gross)}")
            else:
                st.caption(f"Totale tavolo: {eur(gross)}")
        with b3:
            if pending_for_this:
                remaining = max(0, int(float(pending["expires_at"]) - datetime.utcnow().timestamp()))
                st.markdown(
                    f"""
                    <div class='reveal-box'>
                        <div class='reveal-title'>{html.escape(a['name'])}</div>
                        Hai <b>{remaining} secondi</b> per confermare questa prenotazione.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                c_confirm, c_cancel = st.columns(2)
                with c_confirm:
                    if st.button("Conferma ora", key=f"confirm_{a['id']}", type="primary", use_container_width=True, disabled=blocked):
                        if user["membership_status"] != "premium":
                            st.error("Serve una membership premium attiva per prenotare.")
                        elif datetime.utcnow().timestamp() > float(pending["expires_at"]):
                            st.session_state.pop("pending_booking", None)
                            st.error("Tempo scaduto. Seleziona nuovamente il tavolo.")
                            st.rerun()
                        else:
                            try:
                                create_booking_if_available(int(a["id"]), int(user["id"]), str(user["name"]), int(guests_requested), float(gross), float(a["restaurant_fee"]))
                                st.session_state.pop("pending_booking", None)
                                st.success(f"Prenotazione confermata. Il ristorante reale è: {a['name']}.")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.session_state.pop("pending_booking", None)
                                st.warning("Questo tavolo è stato appena prenotato da un altro utente.")
                                st.rerun()
                with c_cancel:
                    if st.button("Annulla", key=f"abort_{a['id']}", use_container_width=True):
                        st.session_state.pop("pending_booking", None)
                        st.rerun()
            else:
                if st.button("Prenota esperienza", key=f"book_{a['id']}", type="primary", use_container_width=True, disabled=blocked):
                    if user["membership_status"] != "premium":
                        st.error("Serve una membership premium attiva per prenotare.")
                    elif cancellation_count(int(user["id"])) >= 2:
                        st.error("Prenotazioni bloccate dopo 2 cancellazioni.")
                    else:
                        st.session_state.pending_booking = {
                            "availability_id": int(a["id"]),
                            "guest_count": int(guests_requested),
                            "expires_at": datetime.utcnow().timestamp() + 60,
                        }
                        st.rerun()

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
    if user["role"] == "customer":
        cancels = cancellation_count(int(user["id"]))
        st.markdown(f"### Cancellazioni ({cancels}/2)")
        future_confirmed = [r for r in rows if r["status"] == "confirmed" and r["service_date"] >= str(date.today())]
        if future_confirmed:
            st.caption("Puoi cancellare una prenotazione futura. Dopo 2 cancellazioni il marketplace blocca nuove prenotazioni.")
            for r in future_confirmed:
                c_info, c_btn = st.columns([3, 1])
                with c_info:
                    st.write(f"**{r['restaurant']}** · {r['service_date']} {r['service_time']} · {r['guests']} persone")
                with c_btn:
                    if st.button("Cancella", key=f"cancel_booking_{r['id']}", use_container_width=True):
                        if cancel_booking(int(r["id"]), int(user["id"])):
                            st.success("Prenotazione cancellata. Il tavolo è tornato disponibile.")
                            st.rerun()
                        else:
                            st.error("Non è possibile cancellare questa prenotazione.")
        else:
            st.caption("Nessuna prenotazione futura cancellabile.")
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
    gallery_cols = st.columns(3)
    for idx, r in enumerate(rows):
        with gallery_cols[idx % 3]:
            st.markdown(
                f"""
                <div class='secret-card'>
                    <div class='secret-img' style="background-image:url('{restaurant_image_uri(r['id'])}')"></div>
                    <div class='card-body-dark'>
                        <span class='badge badge-green'>{r['stars']}★ Michelin</span>
                        <span class='badge badge-blue'>{html.escape(r['city'])}</span>
                        <div class='restaurant-name'>{html.escape(r['name'])}</div>
                        <p class='small-muted'>{html.escape(r['area'])} · Taste {html.escape(r['taste'])}</p>
                        <p>Rating <b style='color:#f4d98f'>{r['avg_rating']}</b> · {'Attivo' if r['active'] else 'Non attivo'}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("### Tabella operativa")
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
    st.markdown("""
        <style>
        .stNumberInput input, .stTextInput input, .stTextArea textarea, .stDateInput input { background:#ffffff !important; color:#000000 !important; -webkit-text-fill-color:#000000 !important; }
        .stNumberInput input::placeholder, .stTextInput input::placeholder, .stTextArea textarea::placeholder { color:#444444 !important; opacity:1 !important; }
        div[data-baseweb="select"] * { color:#000000 !important; }
        div[data-testid="stExpander"] label, div[data-testid="stExpander"] p { color:#000000 !important; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("## Business case interattivo")
    st.markdown("Modifica le leve operative e verifica in tempo reale prenotazioni, GBV, ricavi da fee, ricavi subscription e potenziale di scala. Il modello riprende la logica subscription + success fee del business case originale.")

    st.markdown("<div class='calc-hero'><h3 style='margin-top:0'>Simulator Lombardia / Italia</h3><p>Usa gli input per costruire scenari Low, Base, High o personalizzati. Le formule sono volutamente trasparenti per poter discutere pricing, crescita e unit economics con ristoranti e investitori.</p></div>", unsafe_allow_html=True)

    with st.expander("Input del modello", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            restaurants = st.number_input("Ristoranti attivi", min_value=1, max_value=1000, value=64, step=1)
            tables_per_day = st.number_input("Tavoli per ristorante/giorno", min_value=1, max_value=10, value=1, step=1)
        with c2:
            weeks = st.number_input("Settimane operative/anno", min_value=1, max_value=52, value=50, step=1)
            days_week = st.slider("Giorni vendibili/settimana", 1, 7, 3)
        with c3:
            pax = st.slider("Persone medie per tavolo", 2.0, 4.0, 2.8, 0.1)
            price_pp = st.slider("Prezzo medio per persona", 80, 250, 130, 5)
        with c4:
            fee = st.select_slider("Success fee per tavolo", options=[30, 35, 40, 45, 50], value=50)
            sub_month = st.number_input("Subscription utente mensile", min_value=0.0, max_value=30.0, value=3.99, step=0.50)
        c5, c6, c7 = st.columns(3)
        with c5:
            bookings_per_user_year = st.slider("Prenotazioni/anno per utente pagante", 1.0, 8.0, 2.0, 0.5)
        with c6:
            fill_rate = st.slider("Sell-through disponibilità", 30, 100, 100, 5)
        with c7:
            show_italy = st.toggle("Confronta con scala Italia", value=True)

    theoretical_bookings = restaurants * tables_per_day * weeks * days_week
    bookings = theoretical_bookings * fill_rate / 100
    gbv = bookings * pax * price_pp
    fee_revenue = bookings * fee
    paying_users = bookings / bookings_per_user_year if bookings_per_user_year else 0
    subscription_revenue = paying_users * sub_month * 12
    total_revenue = fee_revenue + subscription_revenue
    restaurant_incremental = gbv - fee_revenue

    kpi_grid([
        ("Prenotazioni annue", int_it(bookings), f"{fill_rate}% sell-through"),
        ("Gross Booking Value", eur(gbv, True), f"{pax:.1f} pax · €{price_pp} pp"),
        ("Ricavi piattaforma", eur(total_revenue, True), "fee + subscription"),
        ("Utenti paganti stimati", int_it(paying_users), f"{bookings_per_user_year:g} pren./anno"),
    ])

    r1, r2 = st.columns([1.1, .9], gap="large")
    with r1:
        st.markdown("### Formula del caso selezionato")
        st.markdown(
            f"""
            <div class='calc-result'>
                <div class='big-number'>{int_it(restaurants)} × {int_it(tables_per_day)} × {int_it(days_week)} × {int_it(weeks)} × {fill_rate}%</div>
                <p style='font-size:1.05rem'>= <b>{int_it(bookings)}</b> prenotazioni annue vendute</p>
                <table class='app-table'>
                    <tr><th>Voce</th><th>Valore</th></tr>
                    <tr><td>Ricavi da success fee</td><td><b>{eur(fee_revenue)}</b></td></tr>
                    <tr><td>Ricavi da subscription</td><td><b>{eur(subscription_revenue)}</b></td></tr>
                    <tr><td>Totale ricavi piattaforma</td><td><b>{eur(total_revenue)}</b></td></tr>
                    <tr><td>Valore incrementale lordo per i ristoranti</td><td><b>{eur(restaurant_incremental)}</b></td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown("### Mix ricavi")
        fee_pct = int(round((fee_revenue / total_revenue) * 100)) if total_revenue else 0
        sub_pct = 100 - fee_pct if total_revenue else 0
        st.markdown(
            f"""
            <div class='panel'>
                <h3>Fee ristorante</h3>
                <div class='progress-shell'><div class='progress-fill' style='width:{fee_pct}%'></div></div>
                <p><b>{fee_pct}%</b> · {eur(fee_revenue)}</p>
                <h3>Subscription utenti</h3>
                <div class='progress-shell'><div class='progress-fill' style='width:{sub_pct}%'></div></div>
                <p><b>{sub_pct}%</b> · {eur(subscription_revenue)}</p>
                <p class='small-muted'>Il modello resta allineato agli interessi dei ristoranti: la piattaforma guadagna quando il tavolo viene confermato.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Scenari automatici")
    scenario_rows = []
    for name, d in [("Low", 2), ("Base", 3), ("High", 4)]:
        b = restaurants * tables_per_day * weeks * d * fill_rate / 100
        users = b / bookings_per_user_year if bookings_per_user_year else 0
        sub = users * sub_month * 12
        total_30 = b * 30 + sub
        total_50 = b * 50 + sub
        scenario_rows.append([name, d, int_it(b), eur(b * pax * price_pp, True), eur(total_30), eur(total_50)])
    st.markdown(table_html(["Scenario", "Giorni/sett.", "Prenotazioni", "GBV", "Ricavi fee €30", "Ricavi fee €50"], scenario_rows, {0, 4, 5}), unsafe_allow_html=True)

    st.markdown("### Sensibilità principali")
    sens_html = "<div class='sensitivity-grid'>"
    for label, fee_x, days_x in [("Conservativo", 30, 2), ("Base premium", 50, 3), ("Espansivo", 50, 4)]:
        b = restaurants * tables_per_day * weeks * days_x * fill_rate / 100
        users = b / bookings_per_user_year if bookings_per_user_year else 0
        total = b * fee_x + users * sub_month * 12
        sens_html += f"<div class='dark-card'><div class='card-title'>{label}</div><p>{days_x} giorni/settimana · fee €{fee_x}</p><h2 style='color:#f4d98f'>{eur(total, True)}</h2><p>{int_it(b)} prenotazioni annue</p></div>"
    sens_html += "</div>"
    st.markdown(sens_html, unsafe_allow_html=True)

    if show_italy:
        st.markdown("### Scala Italia")
        italy_restaurants = 394
        italy_bookings = italy_restaurants * tables_per_day * weeks * days_week * fill_rate / 100
        italy_gbv = italy_bookings * pax * price_pp
        italy_users = italy_bookings / bookings_per_user_year if bookings_per_user_year else 0
        italy_sub = italy_users * sub_month * 12
        italy_total = italy_bookings * fee + italy_sub
        st.markdown(
            f"""
            <div class='calc-result'>
                <div class='big-number'>394 × {int_it(days_week)} × {int_it(weeks)} = {int_it(italy_bookings)}</div>
                <p>Prenotazioni annue potenziali Italia con gli stessi parametri operativi.</p>
                <table class='app-table'>
                    <tr><th>Voce</th><th>Valore</th></tr>
                    <tr><td>GBV Italia stimato</td><td><b>{eur(italy_gbv, True)}</b></td></tr>
                    <tr><td>Ricavi subscription Italia</td><td><b>{eur(italy_sub, True)}</b></td></tr>
                    <tr><td>Ricavi piattaforma Italia</td><td><b>{eur(italy_total, True)}</b></td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='alert-green'>✓ <span>Il simulatore permette di presentare il business case in modo dinamico: cambiando ristoranti, frequenza, prezzo, fee e membership si vede immediatamente l'impatto su ricavi e liquidità del marketplace.</span></div>", unsafe_allow_html=True)

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
    top_navigation()
    page = st.session_state.get("page", page)
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
