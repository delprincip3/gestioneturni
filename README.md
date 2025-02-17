# Gestione Turni - Il Boschetto

Sistema di gestione turni per il ristorante Il Boschetto. Un'applicazione web moderna e intuitiva per la gestione del personale e dei turni di lavoro.

## Caratteristiche Principali

### Autenticazione e Sicurezza
- Sistema di login sicuro con protezione CSRF
- Gestione password con hashing sicuro (pbkdf2:sha256)
- Sistema di recupero password via email con generazione password casuale
- Sessioni utente protette (durata 5 minuti)
- Ruoli utente (admin/user) con autorizzazioni differenziate
- Rate limiting per prevenire attacchi brute force
- Logging di sicurezza con rotazione dei file

### Gestione Utenti (Admin)
- Dashboard admin dedicata
- Registrazione nuovi utenti con ruoli specifici
- Modifica e eliminazione utenti esistenti
- Gestione profili utente completa
- Notifiche email automatiche per:
  - Creazione nuovo account
  - Modifica dati utente
  - Reset password
  - Cambio password

### Gestione Turni (Admin)
- Creazione e assegnazione turni
- Visualizzazione turni in formato tabella con:
  - Filtri avanzati per data, tipo turno, ruolo, utente
  - Paginazione intelligente (10 turni per pagina)
  - Ordinamento per data
- Modifica e eliminazione turni
- Gestione assenze del personale con:
  - Notifiche immediate agli admin
  - Sistema di marcatura assenze come gestite
  - Storico comunicazioni
- Sistema di notifiche email per:
  - Nuovi turni assegnati
  - Modifiche ai turni
  - Eliminazione turni
  - Comunicazioni di assenza

### Area Utente
- Dashboard personalizzata
- Visualizzazione turni personali con filtri avanzati
- Sistema di comunicazione assenze
- Gestione profilo personale
- Cambio password sicuro con notifica email

### Interfaccia Utente
- Design responsive e moderno con Tailwind CSS
- Tema personalizzato con i colori del brand
- Componenti UI ottimizzati:
  - Menu di navigazione adattivo
  - Accordion per sezioni collassabili
  - Modal per azioni importanti
  - Toast notifications con SweetAlert2
  - Form validati lato client e server
- Feedback visivi per tutte le azioni

## Stack Tecnologico

### Backend
- Python 3.12+
- Flask Framework
- SQLAlchemy ORM
- Flask-Mail per email
- Flask-WTF per form e CSRF
- Flask-Migrate per migrazioni database
- Flask-Limiter per rate limiting
- Python-dotenv per configurazione
- Psycopg2-binary per PostgreSQL
- Gunicorn per server WSGI

### Frontend
- HTML5 + CSS3
- Tailwind CSS 3.4+
- DaisyUI per componenti
- Font Awesome 6.0+
- SweetAlert2 per notifiche
- JavaScript ES6+

### Database
- PostgreSQL 16+

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/tuouser/gestioneturni.git
cd gestioneturni
```

2. Crea e attiva un ambiente virtuale:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installa le dipendenze Python:
```bash
pip install -r requirements.txt
```

4. Installa le dipendenze npm:
```bash
npm install
```

5. Copia il file `.env.example` in `.env` e configura le variabili:
```bash
cp .env.example .env
```

6. Configura le seguenti variabili nel file `.env`:
```
# Database
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gestioneturni_boschetto

# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False

# Admin di Default
ADMIN_EMAIL=your_admin_email
ADMIN_PASSWORD=your_admin_password
ADMIN_NOME=your_admin_name
ADMIN_COGNOME=your_admin_surname

# Supporto App
SUPPORT_LINK=your_support_link
```

7. Inizializza il database:
```bash
flask db upgrade
```

8. Avvia il server di sviluppo:
```bash
flask run --port=2001
```

9. In un altro terminale, avvia il compilatore CSS:
```bash
npm run dev
```

## Deployment su Render

1. Crea un nuovo database PostgreSQL su Render
2. Configura le seguenti variabili d'ambiente nel web service:
   - Tutte le variabili DB_* dal database PostgreSQL creato
   - MAIL_* per la configurazione email
   - ADMIN_* per le credenziali dell'amministratore
   - SUPPORT_LINK per il link di supporto
   - PYTHON_VERSION=3.12.1
   - FLASK_APP=app.py
   - FLASK_ENV=production
   - SECRET_KEY (generato automaticamente)

3. Il file `build.sh` si occuperà di:
   - Installare le dipendenze Python
   - Installare le dipendenze npm
   - Compilare il CSS
   - Eseguire le migrazioni del database

4. Il comando di start `gunicorn app:app` avvierà l'applicazione

## Utilizzo

1. Configura le credenziali dell'amministratore nel file `.env`
2. Crea nuovi utenti dalla sezione "Gestione Utenti"
3. Assegna i turni dalla sezione "Gestione Turni"
4. Gli utenti riceveranno notifiche email per ogni azione rilevante
5. Il link di supporto sarà disponibile nell'header dell'applicazione

## Contribuire

1. Fai il fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome-feature`)
3. Committa i tuoi cambiamenti (`git commit -am 'Aggiungi feature'`)
4. Pusha al branch (`git push origin feature/nome-feature`)
5. Crea una Pull Request

## Supporto

L'applicazione include una funzionalità di supporto che permette agli utenti di contribuire al suo sviluppo. Il link di supporto è personalizzabile attraverso la variabile d'ambiente `SUPPORT_LINK` e sarà visibile nell'header dell'applicazione.

## Licenza

Copyright © 2024 - Tutti i diritti riservati da Luigi Michele Del Principe