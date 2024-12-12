from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta
from forms import LoginForm, RegisterForm, EliminaUtenteForm, ModificaUtenteForm, GestisciTurniForm, CambiaPasswordForm
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
import base64
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

load_dotenv()  # Carica le variabili d'ambiente prima di configurare l'app

app = Flask(__name__, template_folder='src', static_folder='src')
app.permanent_session_lifetime = timedelta(minutes=5)

# Configurazione del database usando variabili d'ambiente
DB_USERNAME = os.environ.get('DB_USERNAME', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Luigi2005')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'gestioneturni_boschetto')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USERNAME = 'delprincipeluigimichele@gmail.com',
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD'),
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_MAX_EMAILS = 5,
    MAIL_TIMEOUT = 30,
    MAIL_DEFAULT_SENDER = ('Il Boschetto - No Reply', 'delprincipeluigimichele@gmail.com')
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

csrf = CSRFProtect(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Non è necessario un context processor per il CSRF token

class Utenza(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
  
    def __init__(self, tipo, nome, cognome, email, password):
        self.tipo = tipo
        self.nome = nome
        self.cognome = cognome
        self.email = email
        # Hash della password solo se non è già hashata
        if len(password) < 50:  # Le password hashate sono più lunghe
            self.password = generate_password_hash(password)
        else:
            self.password = password

class Turno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    turno = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    utenza_id = db.Column(db.Integer, db.ForeignKey('utenza.id'), nullable=False)

    utenza = db.relationship('Utenza', backref=db.backref('turni', lazy=True))

    def __repr__(self):
        return f"<Turno {self.data} {self.turno} {self.tipo}>"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login per accedere a questa pagina.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login per accedere a questa pagina.', 'danger')
            return redirect(url_for('login'))
        
        user = Utenza.query.get(session['user_id'])
        if not user or user.tipo != 'admin':
            flash('Non hai i permessi per accedere a questa pagina.', 'danger')
            return redirect(url_for('dashboard_user'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if 'user_id' in session:
        user = Utenza.query.get(session['user_id'])
        if user.tipo == 'admin':
            return redirect(url_for('dashboard_admin'))
        return redirect(url_for('dashboard_user'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Utenza.query.filter_by(email=form.email.data).first()
        
        try:
            # Per le password non ancora hashate
            if len(user.password) < 50:  # Le password hashate sono più lunghe
                if user.password == form.password.data:
                    # Aggiorna la password con hash
                    user.password = generate_password_hash(form.password.data)
                    db.session.commit()
                    login_successful = True
                else:
                    login_successful = False
            else:
                # Per le password già hashate
                login_successful = check_password_hash(user.password, form.password.data)

            if login_successful:
                session.clear()
                session['user_id'] = user.id
                session['user_type'] = user.tipo
                session['_fresh'] = True
                session.permanent = True
                
                app.logger.info(f'Login riuscito per utente {user.email}')
                
                if user.tipo == 'admin':
                    return redirect(url_for('dashboard_admin'))
                return redirect(url_for('dashboard_user'))
            
        except Exception as e:
            app.logger.error(f'Errore durante il login: {str(e)}')
            
        app.logger.warning(f'Tentativo di login fallito per email {form.email.data}')
        flash('Email o password non validi.', 'danger')
        
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout eseguito con successo!', 'success')
    return redirect(url_for('login'))


@app.route('/dashboardadmin')
@admin_required
def dashboard_admin():
    return render_template('dashboard_admin.html')

@app.route('/dashboarduser')
@login_required
def dashboard_user():
    return render_template('dashboard_user.html')

@app.route('/turni', methods=['GET', 'POST'])
def gestisci_turni():
    if 'user_id' not in session:
        flash('Devi essere loggato per vedere questa pagina.', 'danger')
        return redirect(url_for('login'))

    form = GestisciTurniForm()
    form.utenza_id.choices = [(utente.id, f"{utente.nome} {utente.cognome}") for utente in Utenza.query.all()]
    
    if request.method == 'POST' and form.validate_on_submit():
        data = form.data.data
        turno = form.turno.data
        tipo = form.tipo.data
        utenza_id = form.utenza_id.data

        nuovo_turno = Turno(data=data, turno=turno, tipo=tipo, utenza_id=utenza_id)
        db.session.add(nuovo_turno)
        db.session.commit()
        flash('Turno aggiunto con successo!', 'success')

    turni = Turno.query.all()
    return render_template('gestisci_turni.html', form=form, turni=turni)

@app.route('/gestisci_utenti', methods=['GET'])
def gestisci_utenti():
    if 'user_id' not in session:
        flash('Devi essere loggato per vedere questa pagina.', 'danger')
        return redirect(url_for('login'))

    modifica_form = ModificaUtenteForm()
    elimina_form = EliminaUtenteForm()
    register_form = RegisterForm()

    utenti = Utenza.query.all()
    return render_template('gestisci_utenti.html', modifica_form=modifica_form, elimina_form=elimina_form,register_form=register_form, utenti=utenti)



@app.route('/elimina_utente', methods=['POST'])
def elimina_utente():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Devi essere loggato per vedere questa pagina."}), 403

    data = request.get_json()
    utente_id = data.get('id')
    elimina_form = EliminaUtenteForm()

    if elimina_form.validate_on_submit():
        utente = Utenza.query.get(utente_id)
        if utente:
            Turno.query.filter_by(utenza_id=utente_id).delete()
            db.session.delete(utente)
            db.session.commit()
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Utente non trovato."}), 404
    else:
        return jsonify({"success": False, "error": "Errore nella validazione del form."}), 400
    
@app.route('/aggiungi_utente', methods=['POST'])
def aggiungi_utente():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non autorizzato'}), 403

    try:
        # Verifica CSRF token
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            csrf_token = request.form.get('csrf_token')
        
        if not csrf_token:
            return jsonify({'success': False, 'message': 'Token CSRF mancante'}), 400

        tipo = request.form.get('tipo')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([tipo, nome, cognome, email, password]):
            return jsonify({'success': False, 'message': 'Tutti i campi sono obbligatori'}), 400

        # Normalizza il tipo utente
        tipo = tipo.lower()
        if tipo not in ['admin', 'user']:
            return jsonify({'success': False, 'message': 'Tipo utente non valido'}), 400

        # Verifica se l'email esiste già
        if Utenza.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email già registrata'}), 400

        # Crea il nuovo utente
        nuovo_utente = Utenza(
            tipo=tipo,
            nome=nome,
            cognome=cognome,
            email=email,
            password=password
        )
        
        db.session.add(nuovo_utente)
        db.session.commit()

        # Template email
        template = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #6d28d9; text-align: center;">Benvenuto in Il Boschetto!</h2>
            <p>Gentile {nome},</p>
            <p>Ti diamo il benvenuto nel nostro team. Di seguito trovi le tue credenziali di accesso al sistema:</p>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Password:</strong> {password}</p>
            </div>
            
            <p>Per accedere al sistema, visita: <a href="http://localhost:2001/login" style="color: #6d28d9;">http://localhost:2001/login</a></p>
            
            <p>Per motivi di sicurezza, ti consigliamo di cambiare la password al primo accesso.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="color: #6B7280; font-size: 0.875rem;">
                    Questa è un'email generata automaticamente, ti preghiamo di non rispondere.<br>
                    Per assistenza, contatta il tuo supervisore.
                </p>
            </div>
        </div>
        """

        # Invia email
        email_sent = send_email(
            to=email,
            subject='Il Boschetto - Le tue credenziali di accesso',
            template=template
        )
        
        return jsonify({
            'success': True,
            'message': 'Utente aggiunto con successo' + (' e email inviata' if email_sent else ' ma errore nell\'invio email'),
            'user': {
                'id': nuovo_utente.id,
                'nome': nuovo_utente.nome,
                'cognome': nuovo_utente.cognome,
                'email': nuovo_utente.email
            }
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore durante l\'aggiunta dell\'utente: {str(e)}')
        return jsonify({'success': False, 'message': 'Errore durante l\'aggiunta dell\'utente'}), 500

@app.route('/miei_turni')
def miei_turni():
    if 'user_id' not in session:
        flash('Devi essere loggato per vedere questa pagina.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    utente = Utenza.query.get(user_id)
    turni = Turno.query.filter_by(utenza_id=user_id).all()
    return render_template('miei_turni.html', utente=utente, turni=turni)

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

def update_existing_passwords():
    with app.app_context():
        users = Utenza.query.all()
        for user in users:
            if len(user.password) < 50:  # Password non ancora hashata
                user.password = generate_password_hash(user.password)
        db.session.commit()

@app.route('/cambia_password', methods=['GET', 'POST'])
@login_required
def cambia_password():
    form = CambiaPasswordForm()
    if request.method == 'GET':
        return render_template('cambia_password.html', form=form)
        
    if form.validate_on_submit():
        user = Utenza.query.get(session['user_id'])
        
        if check_password_hash(user.password, form.password_attuale.data):
            user.password = generate_password_hash(form.nuova_password.data)
            db.session.commit()
            
            # Configurazione Mailtrap per test email
            app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
            app.config['MAIL_PORT'] = 2525
            app.config['MAIL_USERNAME'] = 'your_mailtrap_username'
            app.config['MAIL_PASSWORD'] = 'your_mailtrap_password'
            app.config['MAIL_USE_TLS'] = True
            app.config['MAIL_USE_SSL'] = False
            
            try:
                msg = Message(
                    'Il Boschetto - Conferma cambio password',
                    sender=('Il Boschetto - No Reply', 'noreply@ilboschetto.com'),
                    recipients=[user.email]
                )
                
                msg.html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <img src="cid:logo" alt="Il Boschetto Logo" style="width: 150px; height: auto;">
                    </div>
                    <h2 style="color: #6d28d9; text-align: center;">Password Modificata</h2>
                    <p>Gentile {user.nome},</p>
                    <p>La tua password è stata modificata con successo.</p>
                    <p>Se non hai effettuato tu questa modifica, contatta immediatamente il tuo supervisore.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="color: #6B7280; font-size: 0.875rem;">
                            Questa è un'email generata automaticamente, ti preghiamo di non rispondere.<br>
                            Per assistenza, contatta il tuo supervisore.
                        </p>
                    </div>
                </div>
                """
                
                with app.open_resource("src/logoboschetto.jpeg") as logo:
                    msg.attach("logoboschetto.jpeg", "image/jpeg", logo.read(), "inline", headers=[["Content-ID", "<logo>"]])
                
                mail.send(msg)
                
            except Exception as e:
                app.logger.error(f'Errore nell\'invio dell\'email di conferma cambio password: {str(e)}')
            
            return jsonify({'success': True, 'message': 'Password modificata con successo!'})
        else:
            return jsonify({'success': False, 'message': 'Password attuale non corretta'})
    
    return jsonify({'success': False, 'message': 'Dati non validi'}), 400

# Configurazione del logging
if not app.debug:
    file_handler = RotatingFileHandler('security.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Applicazione avviata')

def send_email(to, subject, template):
    try:
        # Crea il messaggio
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = 'Il Boschetto - No Reply <delprincipeluigimichele@gmail.com>'
        msg['To'] = to
        
        # Aggiungi il logo come immagine base64
        try:
            with app.open_resource("src/logoboschetto.jpeg", "rb") as logo:
                logo_base64 = base64.b64encode(logo.read()).decode()
                template = template.replace('<h2', f'''
                    <div style="text-align: center; margin-bottom: 20px;">
                        <img src="data:image/jpeg;base64,{logo_base64}" alt="Il Boschetto Logo" style="width: 150px; height: auto;">
                    </div>
                    <h2''')
        except Exception as e:
            app.logger.error(f'Errore nella codifica del logo: {str(e)}')

        # Aggiungi il contenuto HTML
        html_part = MIMEText(template, 'html')
        msg.attach(html_part)

        # Configura la connessione SMTP
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
                    server.starttls()
                    server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
                    server.send_message(msg)
                    app.logger.info(f'Email inviata con successo a {to}')
                    return True
            except Exception as e:
                if attempt == max_retries - 1:  # Ultimo tentativo
                    raise
                app.logger.warning(f'Tentativo {attempt + 1} fallito: {str(e)}')
                time.sleep(2)
        
    except Exception as e:
        app.logger.error(f'Errore nell\'invio dell\'email a {to}: {str(e)}')
        return False

def test_smtp_connection():
    try:
        with smtplib.SMTP('sandbox.smtp.mailtrap.io', 587) as server:
            server.starttls()
            server.login('8e8ce25bbe09b6', 'b4e3d8aa8d')
            print("Connessione riuscita!")
            return True
    except Exception as e:
        print(f"Errore: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp_connection()
    update_existing_passwords()
    app.run(debug=True,port=2001)
