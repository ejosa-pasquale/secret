# Secret Star Restaurant - Streamlit

Applicazione Streamlit autonoma per il marketplace premium di prenotazioni last-minute nei ristoranti stellati.

## File principale per Streamlit Cloud

```text
streamlit_app.py
```

## Avvio locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Su Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy su Streamlit Community Cloud

1. Carica tutti i file nella root del repository GitHub.
2. Su Streamlit Cloud seleziona il repository.
3. Imposta **Main file path** a:

```text
streamlit_app.py
```

4. Verifica che `requirements.txt` e `runtime.txt` siano nella stessa cartella di `streamlit_app.py`.

## Credenziali demo

```text
Admin:    admin@secretstar.local / Admin123!
Manager:  manager@secretstar.local / Manager123!
Cliente:  cliente@secretstar.local / Cliente123!
```

## Dipendenze

Questa versione usa solo:

```text
streamlit
sqlite3 standard library
hashlib standard library
```

Non usa Plotly, SQLAlchemy o bcrypt per evitare errori di installazione su Streamlit Cloud.

## Funzionalita incluse

- Login e registrazione cliente
- Ruoli admin, restaurant manager e customer
- Dashboard KPI
- Grafico ricavi con `st.line_chart`
- Marketplace last-minute
- Ristorante secret fino alla prenotazione
- Abbonamento monthly/annual
- Prenotazioni collegate al database SQLite
- Gestione ristoranti
- Gestione disponibilita
- Review e qualita
- Database SQLite inizializzato automaticamente
