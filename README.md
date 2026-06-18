# Secret Star Restaurant — Streamlit Black Edition

Applicazione Streamlit pronta per GitHub e Streamlit Community Cloud, aggiornata con una grafica elegante su sfondo nero: card premium, accenti verde/oro, layout responsive desktop/mobile e fotografie differenti per ogni ristorante.

## File principale per Streamlit

```text
streamlit_app.py
```

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Credenziali demo

| Ruolo | Email | Password |
|---|---|---|
| Admin | admin@secretstar.local | Admin123! |
| Manager | manager@secretstar.local | Manager123! |
| Cliente | cliente@secretstar.local | Cliente123! |

## Deploy su Streamlit Cloud

1. Carica tutti i file nella root del repository GitHub.
2. Crea una nuova app su Streamlit Cloud.
3. Imposta `Main file path` su:

```text
streamlit_app.py
```

4. Verifica che nella root ci siano:

```text
streamlit_app.py
requirements.txt
runtime.txt
.streamlit/config.toml
assets/
README.md
```

## Aggiornamenti grafici inclusi

- Tema nero elegante con accenti verde premium e oro.
- Card marketplace ridisegnate per desktop e mobile.
- Immagine diversa per ogni ristorante: `assets/restaurant_1.png` ... `assets/restaurant_8.png`.
- Gallery visuale nella sezione Ristoranti.
- Immagini adattive con `background-size: cover`, overlay scuro e testi leggibili.
- Layout responsive: griglie larghe su desktop e schede verticali su mobile.
- Nessuna dipendenza da Plotly, Altair, Pandas o SQLAlchemy.
- Nessun uso di `st.line_chart`, per evitare errori Altair su Streamlit Cloud.

## Funzionalità

- Login con ruoli admin, manager e customer.
- Dashboard KPI e grafici SVG interni.
- Marketplace con ristorante secret fino alla prenotazione.
- Prenotazioni collegate al database SQLite.
- Review clienti.
- Gestione ristoranti e pubblicazione disponibilità.
- Business case Lombardia e Italia.
- Roadmap 12 mesi.
- Sezione admin per reset demo e manutenzione.
