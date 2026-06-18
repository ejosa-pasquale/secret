# Secret Star Restaurant - Streamlit App

Versione Streamlit della piattaforma **Secret Star Restaurant**, pensata per essere caricata su GitHub e pubblicata su Streamlit Community Cloud.

Il file da indicare a Streamlit e':

```text
streamlit_app.py
```

## Funzionalita'

- Login e registrazione utenti
- Ruoli: admin, restaurant manager, customer
- Marketplace last-minute con ristorante secret fino alla conferma
- Disponibilita' pubblicabili dai ristoranti
- Prenotazioni collegate al database SQLite
- Membership mensile e annuale
- Dashboard con KPI, ricavi, GBV e grafici
- Gestione ristoranti partner
- Review e controllo qualita'
- Database relazionale SQLAlchemy
- Seed demo automatico al primo avvio

## Struttura

```text
secret-star-restaurant-streamlit/
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── src/
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── queries.py
│   ├── seed.py
│   └── ui.py
├── data/
├── docs/
└── tests/
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

## Credenziali demo

```text
Admin:    admin@secretstar.local / Admin123!
Manager:  manager@secretstar.local / Manager123!
Cliente:  cliente@secretstar.local / Cliente123!
```

## Deploy su Streamlit Community Cloud

1. Crea un nuovo repository GitHub.
2. Carica tutti i file di questa cartella.
3. Vai su Streamlit Community Cloud.
4. Seleziona il repository.
5. Nel campo **Main file path** inserisci:

```text
streamlit_app.py
```

6. Avvia il deploy.

## Variabili ambiente

Localmente puoi copiare `.env.example` in `.env`.

```text
DATABASE_URL=sqlite:///data/secret_star.db
```

Su Streamlit Cloud puoi usare i Secrets, ma l'app funziona anche senza configurazione iniziale perche' crea automaticamente il database SQLite.

## Nota tecnica

Questa versione non e' una PWA FastAPI. E' una conversione Streamlit autonoma, adatta a demo, MVP, dashboard e validazione rapida del concept. Per una produzione scalabile multiutente si consiglia di mantenere la versione FastAPI/PWA o collegare Streamlit a PostgreSQL.
