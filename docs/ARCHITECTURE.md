# Architettura Streamlit

L'app e' composta da un entrypoint `streamlit_app.py` e moduli in `src/`.

- `src/models.py`: modelli SQLAlchemy e relazioni.
- `src/database.py`: engine, sessioni e inizializzazione DB.
- `src/auth.py`: hash password, login e creazione utenti.
- `src/queries.py`: funzioni applicative e query aggregate.
- `src/seed.py`: dati demo iniziali.
- `src/ui.py`: CSS e componenti UI riutilizzabili.

Il database SQLite viene creato in `data/secret_star.db`.
