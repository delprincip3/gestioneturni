# gestioneturni# Gestione Turni Boschetto

## Descrizione
Gestione Turni Boschetto è una web application per la gestione dei turni dei dipendenti. Gli amministratori possono aggiungere, modificare e rimuovere utenti, oltre a gestire i turni. Gli utenti registrati possono visualizzare i propri turni.

## Prerequisiti
- Python 3.x
- MySQL Server
- Pipenv (opzionale, per gestione dell'ambiente virtuale)

## Installazione

1. Clona il repository:
    ```bash
    git clone https://github.com/tuo-utente/gestioneturni_boschetto.git
    cd gestioneturni_boschetto
    ```

2. Crea un ambiente virtuale e installa le dipendenze:
    ```bash
    pipenv install
    pipenv shell
    ```

    Oppure usa `venv` e `pip`:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows usa `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Configura il database:
    - Crea un database MySQL chiamato `gestioneturni_boschetto`.
    - Aggiorna la configurazione del database in `app.py` se necessario:
      ```python
      app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Luigi2005@localhost:3306/gestioneturni_boschetto"
      ```

4. Esegui le migrazioni del database:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

5. Avvia l'applicazione:
    ```bash
    flask run
    ```

## Struttura del Progetto

- `app.py`: il file principale dell'applicazione Flask.
- `models.py`: contiene i modelli del database SQLAlchemy.
- `forms.py`: contiene i form WTForms.
- `src/`: contiene i template HTML e i file statici.

## Rotte Principali

- `GET /`: pagina principale.
- `GET/POST /login`: pagina di login.
- `GET /logout`: logout.
- `GET /dashboardadmin`: dashboard per l'amministratore.
- `GET /dashboarduser`: dashboard per gli utenti.
- `GET/POST /turni`: gestione dei turni.
- `GET /gestisci_utenti`: gestione degli utenti.
- `POST /elimina_utente`: eliminazione di un utente (AJAX).
- `POST /aggiungi_utente`: aggiunta di un nuovo utente.
- `GET /miei_turni`: visualizzazione dei turni dell'utente loggato.

## Sicurezza

- Protezione CSRF: abilitata tramite `flask-wtf`.
- Autenticazione e autorizzazione: sessioni utente gestite con Flask-Login.

## Contributi

I contributi sono benvenuti! Sentiti libero di aprire issue e pull request.

## Licenza

Questo progetto è sotto licenza MIT.
