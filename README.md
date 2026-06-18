# Secret Star Restaurant — Streamlit Picture Style

Applicazione Streamlit pronta per GitHub e Streamlit Community Cloud, riscritta con una grafica coerente con il deck "Secret Star Restaurant": verde premium, navy, card scure, alert verde, tabelle editoriali e immagini estratte dal documento fornito.

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

## Note tecniche

- Non usa Plotly, Altair, Pandas o SQLAlchemy.
- Non usa `st.line_chart`, quindi evita l'errore Altair visto su Python 3.14.
- Usa SQLite tramite libreria standard Python.
- Le password demo sono salvate con PBKDF2-HMAC-SHA256.
- Il database viene creato automaticamente al primo avvio.
- I dati su Streamlit Cloud sono dimostrativi e possono essere resettati al riavvio dell'ambiente.

## Funzionalità

- Login con ruoli admin, manager e customer.
- Dashboard KPI e grafici SVG interni.
- Marketplace con ristorante secret fino alla prenotazione.
- Prenotazioni collegate al database.
- Review clienti.
- Gestione ristoranti e pubblicazione disponibilità.
- Business case Lombardia e Italia.
- Roadmap 12 mesi.
- Sezione admin per reset demo e manutenzione.
