# Gestione Turni - Il Boschetto

Sistema di gestione turni per il ristorante Il Boschetto. Un'applicazione web moderna e intuitiva per la gestione del personale e dei turni di lavoro.

## Caratteristiche Principali

### Autenticazione e Sicurezza
- Sistema di login sicuro con protezione CSRF
- Gestione password con hashing sicuro
- Sistema di recupero password via email
- Sessioni utente protette
- Ruoli utente (admin/user) con autorizzazioni differenziate

### Gestione Utenti (Admin)
- Dashboard admin dedicata
- Registrazione nuovi utenti con ruoli specifici
- Modifica e eliminazione utenti esistenti
- Gestione profili utente completa
- Notifiche email automatiche per:
  - Creazione nuovo account
  - Modifica dati utente
  - Reset password

### Gestione Turni (Admin)
- Creazione e assegnazione turni
- Visualizzazione turni in formato tabella con:
  - Filtri avanzati per data, tipo turno, ruolo, utente
  - Paginazione intelligente
  - Ordinamento colonne
- Modifica e eliminazione turni
- Gestione assenze del personale
- Sistema di notifiche email per:
  - Nuovi turni assegnati
  - Modifiche ai turni
  - Eliminazione turni
  - Comunicazioni di assenza

### Area Utente
- Dashboard personalizzata
- Visualizzazione turni personali con filtri
- Sistema di comunicazione assenze
- Gestione profilo personale
- Cambio password sicuro

### Interfaccia Utente
- Design responsive e moderno
- Tema personalizzato con i colori del brand
- Componenti UI ottimizzati:
  - Menu di navigazione adattivo
  - Accordion per sezioni collassabili
  - Modal per azioni importanti
  - Toast notifications
  - Form validati lato client e server
- Feedback visivi per tutte le azioni

## Stack Tecnologico

### Backend
- Python 3.12+
- Flask Framework
- SQLAlchemy ORM
- Flask-Mail per email
- Flask-WTF per form e CSRF
- PyMySQL per database MySQL
- Python-dotenv per configurazione

### Frontend
- HTML5 + CSS3
- Tailwind CSS 3.4+
- DaisyUI per componenti
- Font Awesome 6.0+
- SweetAlert2 per notifiche
- JavaScript ES6+

### Database
- MySQL 8.0+

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
DB_PORT=3306
DB_NAME=gestioneturni_boschetto

# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
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

## Utilizzo

1. Accedi come admin:
   - Email: admin@example.com
   - Password: password

2. Crea nuovi utenti dalla sezione "Gestione Utenti"
3. Assegna i turni dalla sezione "Gestione Turni"
4. Gli utenti riceveranno notifiche email per ogni azione rilevante

## Contribuire

1. Fai il fork del repository
2. Crea un branch per la tua feature (`git checkout -b feature/nome-feature`)
3. Committa i tuoi cambiamenti (`git commit -am 'Aggiungi feature'`)
4. Pusha al branch (`git push origin feature/nome-feature`)
5. Crea una Pull Request

## Licenza
MIT License - Copyright (c) 2024 Luigi Michele Del Principe