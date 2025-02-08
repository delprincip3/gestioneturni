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
```