# Gestione Turni - Il Boschetto

Sistema di gestione turni per il ristorante Il Boschetto.

## Funzionalità

### Gestione Utenti
- Registrazione nuovi utenti (camerieri, cuochi, lavapiatti)
- Gestione profili utente
- Interfaccia admin per la gestione degli utenti

### Gestione Turni
- Creazione e assegnazione turni
- Visualizzazione turni in formato tabella
- Filtri avanzati per:
  - Data
  - Tipo turno (mattina/pomeriggio/sera)
  - Ruolo (cameriere/cuoco/lavapiatti)
  - Utente
- Paginazione (10 turni per pagina)
- Notifiche email per nuovi turni assegnati

### Funzionalità Utente
- Dashboard personalizzata
- Visualizzazione turni personali
- Comunicazione assenze

### Interfaccia
- Design responsive e moderno
- Tema personalizzato con colori del brand
- Navigazione intuitiva con accordion
- Filtri di ricerca avanzati

## Tecnologie Utilizzate
- Flask (Python)
- SQLAlchemy
- Flask-Mail
- Tailwind CSS
- Font Awesome
- SweetAlert2

## Installazione

1. Clona il repository
2. Installa le dipendenze Python:
```bash
pip install -r requirements.txt
```

3. Installa le dipendenze npm:
```bash
npm install
```

4. Configura le variabili d'ambiente nel file `.env`:
```
MAIL_SERVER=
MAIL_PORT=
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_USE_TLS=
DATABASE_URL=
```

5. Inizializza il database:
```bash
flask db upgrade
```

6. Avvia il server di sviluppo:
```bash
flask run
```

7. In un altro terminale, avvia il compilatore CSS:
```bash
npm run dev
```

## Licenza
MIT License - Copyright (c) 2024 Luigi Michele Del Principe