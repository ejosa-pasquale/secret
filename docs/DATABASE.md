# Database

Entita' principali:

- `users`: utenti, ruoli e credenziali hashate.
- `restaurants`: ristoranti stellati partner e alias secret.
- `availabilities`: tavoli last-minute disponibili.
- `bookings`: prenotazioni confermate.
- `subscriptions`: membership utente.
- `reviews`: feedback post-esperienza.

Le relazioni sono gestite tramite chiavi esterne SQLAlchemy.
