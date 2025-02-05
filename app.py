from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta, datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
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
from email.mime.image import MIMEImage
import requests
from sqlalchemy import or_
import random
import string

load_dotenv()  # Carica le variabili d'ambiente prima di configurare l'app

app = Flask(__name__, template_folder='src', static_folder='src')
app.permanent_session_lifetime = timedelta(minutes=5)

# Configurazione email
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

# Aggiungi funzioni al contesto globale di Jinja2
app.jinja_env.globals.update(min=min)

mail = Mail(app)

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

class Assenza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turno_id = db.Column(db.Integer, db.ForeignKey('turno.id'), nullable=False)
    data_comunicazione = db.Column(db.DateTime, default=datetime.now)
    gestita = db.Column(db.Boolean, default=False)
    
    turno = db.relationship('Turno', backref=db.backref('assenza', lazy=True))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi essere loggato per vedere questa pagina.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Devi effettuare il login per accedere a questa pagina.', 'danger')
            return redirect(url_for('login'))
        
        user = db.session.get(Utenza, session['user_id'])
        if not user or user.tipo != 'admin':
            flash('Non hai i permessi per accedere a questa pagina.', 'danger')
            return redirect(url_for('dashboard_user'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('user_type') == 'admin':
            return redirect(url_for('dashboard_admin'))
        return redirect(url_for('dashboard_user'))

    form = LoginForm()
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = form.email.data
            password = form.password.data

        if not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email e password sono richiesti'})
            flash('Email e password sono richiesti', 'danger')
            return render_template('login.html', form=form)

        user = Utenza.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['user_type'] = user.tipo
            session.permanent = True
            
            redirect_url = url_for('dashboard_admin') if user.tipo == 'admin' else url_for('dashboard_user')
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': redirect_url})
            return redirect(redirect_url)
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'Credenziali errate'})
        flash('Credenziali errate', 'danger')

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
        oggi = datetime.now().date()
        
        if data < oggi:
            flash('Non è possibile aggiungere turni per date passate.', 'danger')
            return redirect(url_for('gestisci_turni'))
            
        turno = form.turno.data
        tipo = form.tipo.data
        utenza_id = form.utenza_id.data

        try:
            nuovo_turno = Turno(data=data, turno=turno, tipo=tipo, utenza_id=utenza_id)
            db.session.add(nuovo_turno)
            db.session.commit()

            # Invia email di notifica
            utente = db.session.get(Utenza, utenza_id)
            email_template = f"""
            <h2>Nuovo Turno Assegnato</h2>
            <p>Gentile {utente.nome} {utente.cognome},</p>
            <p>Ti è stato assegnato un nuovo turno:</p>
            <ul>
                <li>Data: {data.strftime('%d/%m/%Y')}</li>
                <li>Turno: {turno}</li>
                <li>Tipo: {tipo}</li>
            </ul>
            <p>Se hai domande, contatta il tuo supervisore.</p>
            """
            
            send_email(
                utente.email,
                "Nuovo Turno Assegnato - Il Boschetto",
                email_template
            )
            
            flash('Turno aggiunto con successo! Email di notifica inviata.', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Errore nell\'aggiunta del turno: {str(e)}')
            flash('Errore durante l\'aggiunta del turno.', 'danger')

    # Gestione filtri
    data_filter = request.args.get('data', '')
    tipo_filter = request.args.get('tipo', '')
    turno_filter = request.args.get('turno', '')
    utente_filter = request.args.get('utente', '')
    stato_filter = request.args.get('stato', '')  # nuovo/passato
    
    # Query base
    query = Turno.query
    
    # Applica i filtri se presenti
    if data_filter:
        try:
            data_cercata = datetime.strptime(data_filter, '%Y-%m-%d').date()
            query = query.filter(Turno.data == data_cercata)
        except ValueError:
            pass
    
    if tipo_filter:
        query = query.filter(Turno.tipo == tipo_filter)
    
    if turno_filter:
        query = query.filter(Turno.turno == turno_filter)
    
    if utente_filter:
        query = query.join(Utenza).filter(
            or_(
                Utenza.nome.ilike(f'%{utente_filter}%'),
                Utenza.cognome.ilike(f'%{utente_filter}%')
            )
        )

    today = datetime.now().date()
    if stato_filter == 'nuovo':
        query = query.filter(Turno.data >= today)
    elif stato_filter == 'passato':
        query = query.filter(Turno.data < today)
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(Turno.data.desc()).paginate(page=page, per_page=per_page, error_out=False)
    turni = pagination.items
    
    # Ottieni tutte le assenze, ordinate per data di comunicazione (più recenti prima)
    assenze = Assenza.query.order_by(Assenza.data_comunicazione.desc()).all()
    
    return render_template('gestisci_turni.html', 
                         form=form, 
                         turni=turni, 
                         today=today, 
                         assenze=assenze,
                         pagination=pagination,
                         data_filter=data_filter,
                         tipo_filter=tipo_filter,
                         turno_filter=turno_filter,
                         utente_filter=utente_filter,
                         stato_filter=stato_filter)

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
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Dati non forniti"}), 400

        utente_id = data.get('id')
        if not utente_id:
            return jsonify({"success": False, "message": "ID utente non fornito"}), 400

        utente = db.session.get(Utenza, utente_id)
        if not utente:
            return jsonify({"success": False, "message": "Utente non trovato"}), 404

        db.session.delete(utente)
        db.session.commit()

        return jsonify({"success": True, "message": "Utente eliminato con successo"})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore durante l\'eliminazione dell\'utente: {str(e)}')
        return jsonify({"success": False, "message": str(e)}), 500
    
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

    # Gestione filtri
    data_filter = request.args.get('data', '')
    tipo_filter = request.args.get('tipo', '')
    turno_filter = request.args.get('turno', '')
    stato_filter = request.args.get('stato', '')  # nuovo/passato
    
    # Query base per i turni dell'utente corrente
    query = Turno.query.filter_by(utenza_id=session['user_id'])
    
    # Applica i filtri se presenti
    if data_filter:
        try:
            data_cercata = datetime.strptime(data_filter, '%Y-%m-%d').date()
            query = query.filter(Turno.data == data_cercata)
        except ValueError:
            pass
    
    if tipo_filter:
        query = query.filter(Turno.tipo == tipo_filter)
    
    if turno_filter:
        query = query.filter(Turno.turno == turno_filter)

    today = datetime.now().date()
    if stato_filter == 'nuovo':
        query = query.filter(Turno.data >= today)
    elif stato_filter == 'passato':
        query = query.filter(Turno.data < today)
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(Turno.data.desc()).paginate(page=page, per_page=per_page, error_out=False)
    turni = pagination.items

    return render_template('miei_turni.html', 
                         turni=turni, 
                         today=today,
                         pagination=pagination,
                         data_filter=data_filter,
                         tipo_filter=tipo_filter,
                         turno_filter=turno_filter,
                         stato_filter=stato_filter)

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

def send_email(to, subject, template_html):
    try:
        # Crea il messaggio
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = app.config['MAIL_DEFAULT_SENDER'][1]
        msg['To'] = to

        # Template HTML base standard per tutte le email
        html = f"""
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f9fafb;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: linear-gradient(to right, #7c3aed, #4c1d95);
                    border-radius: 8px 8px 0 0;
                }}
                .logo {{
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    margin-bottom: 15px;
                }}
                .title {{
                    color: #ffffff;
                    font-size: 24px;
                    margin: 0;
                }}
                .content {{
                    padding: 20px;
                    color: #374151;
                }}
                .info-box {{
                    background-color: #f3f4f6;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 15px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: linear-gradient(to right, #7c3aed, #4c1d95);
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #6b7280;
                    font-size: 12px;
                    border-top: 1px solid #e5e7eb;
                    margin-top: 30px;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                li {{
                    padding: 8px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                li:last-child {{
                    border-bottom: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="cid:logo" alt="Il Boschetto Logo" class="logo">
                    <h1 class="title">Il Boschetto</h1>
                </div>
                <div class="content">
                    {template_html}
                </div>
                <div class="footer">
                    <p>Questa è un'email generata automaticamente, ti preghiamo di non rispondere.</p>
                    <p>Per assistenza, contatta il tuo supervisore.</p>
                    <p>© 2024 Il Boschetto - Tutti i diritti riservati</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Aggiungi il contenuto HTML
        msg.attach(MIMEText(html, 'html'))

        # Allega il logo
        with open("src/logoboschetto.jpeg", "rb") as f:
            logo = MIMEImage(f.read())
            logo.add_header('Content-ID', '<logo>')
            logo.add_header('Content-Disposition', 'inline', filename="logoboschetto.jpeg")
            msg.attach(logo)

        # Configura la connessione SMTP
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        
        # Invia l'email
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        app.logger.error(f'Errore nell\'invio email a {to}: {str(e)}')
        return False

def test_smtp_connection():
    try:
        with mail.connect() as conn:
            app.logger.info('Connessione SMTP testata con successo')
    except Exception as e:
        app.logger.error(f'Errore nella connessione SMTP: {str(e)}')

@app.route('/elimina_turno', methods=['POST'])
@login_required
def elimina_turno():
    try:
        data = request.get_json()
        turno_id = data.get('id')
        
        turno = db.session.get(Turno, turno_id)
        if not turno:
            return jsonify({"success": False, "message": "Turno non trovato"}), 404
            
        # Controlla se il turno è modificabile (non nel passato)
        data_turno = turno.data
        oggi = datetime.now().date()
        if data_turno < oggi:
            return jsonify({
                "success": False, 
                "message": "Non è possibile eliminare turni passati"
            }), 400
            
        # Ottieni i dettagli dell'utente per l'email
        utente = db.session.get(Utenza, turno.utenza_id)
        
        # Prepara il template dell'email
        email_template = f"""
        <h2>Notifica Eliminazione Turno</h2>
        <p>Gentile {utente.nome} {utente.cognome},</p>
        <p>Ti informiamo che il tuo turno è stato eliminato:</p>
        <div class="info-box">
            <ul>
                <li><strong>Data:</strong> {turno.data.strftime('%d/%m/%Y')}</li>
                <li><strong>Turno:</strong> {turno.turno}</li>
                <li><strong>Tipo:</strong> {turno.tipo}</li>
            </ul>
        </div>
        <p>Se non hai richiesto questa modifica, contatta immediatamente il tuo supervisore.</p>
        """
        
        # Prima elimina tutte le assenze associate al turno
        assenze = Assenza.query.filter_by(turno_id=turno_id).all()
        for assenza in assenze:
            db.session.delete(assenza)
            
        # Poi elimina il turno
        db.session.delete(turno)
        db.session.commit()
        
        # Invia email di notifica
        send_email(
            utente.email,
            "Notifica Eliminazione Turno - Il Boschetto",
            email_template
        )
        
        return jsonify({"success": True, "message": "Turno eliminato con successo"}), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nell\'eliminazione del turno: {str(e)}')
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/modifica_turno', methods=['POST'])
@login_required
def modifica_turno():
    try:
        data = request.get_json()
        turno_id = data.get('id')
        nuova_data = parse(data.get('data')).date()
        nuovo_turno = data.get('turno')
        nuovo_tipo = data.get('tipo')
        nuovo_utente_id = data.get('utenza_id')
        
        turno = db.session.get(Turno, turno_id)
        if not turno:
            return jsonify({"success": False, "message": "Turno non trovato"}), 404
            
        # Controlla se il turno è modificabile
        data_turno = turno.data
        oggi = datetime.now().date()
        if data_turno < oggi:
            return jsonify({
                "success": False, 
                "message": "Non è possibile modificare turni passati"
            }), 400
            
        # Ottieni i dettagli degli utenti per le email
        vecchio_utente = db.session.get(Utenza, turno.utenza_id)
        nuovo_utente = db.session.get(Utenza, nuovo_utente_id)
        
        # Salva i vecchi dati per l'email
        vecchia_data = turno.data
        vecchio_turno_tipo = turno.turno
        vecchio_tipo = turno.tipo
        
        # Se c'è un'assenza associata, marcala come gestita
        assenza = db.session.get(Assenza, turno_id)
        if assenza:
            assenza.gestita = True
        
        # Aggiorna il turno
        turno.data = nuova_data
        turno.turno = nuovo_turno
        turno.tipo = nuovo_tipo
        turno.utenza_id = nuovo_utente_id
        
        db.session.commit()
        
        # Prepara e invia email al vecchio utente
        if vecchio_utente.id != nuovo_utente.id:
            email_template_vecchio = f"""
            <h2>Notifica Modifica Turno</h2>
            <p>Gentile {vecchio_utente.nome} {vecchio_utente.cognome},</p>
            <p>Ti informiamo che il tuo turno è stato modificato e assegnato a un altro utente:</p>
            <ul>
                <li>Data: {vecchia_data.strftime('%d/%m/%Y')}</li>
                <li>Turno: {vecchio_turno_tipo}</li>
                <li>Tipo: {vecchio_tipo}</li>
            </ul>
            <p>Se non hai richiesto questa modifica, contatta immediatamente il tuo supervisore.</p>
            """
            
            send_email(
                vecchio_utente.email,
                "Notifica Modifica Turno - Il Boschetto",
                email_template_vecchio
            )
        
        # Prepara e invia email al nuovo utente
        email_template_nuovo = f"""
        <h2>Notifica Nuovo Turno</h2>
        <p>Gentile {nuovo_utente.nome} {nuovo_utente.cognome},</p>
        <p>Ti è stato assegnato un nuovo turno:</p>
        <ul>
            <li>Data: {nuova_data.strftime('%d/%m/%Y')}</li>
            <li>Turno: {nuovo_turno}</li>
            <li>Tipo: {nuovo_tipo}</li>
        </ul>
        <p>Se hai domande, contatta il tuo supervisore.</p>
        """
        
        send_email(
            nuovo_utente.email,
            "Notifica Nuovo Turno - Il Boschetto",
            email_template_nuovo
        )
        
        return jsonify({"success": True, "message": "Turno modificato con successo"}), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nella modifica del turno: {str(e)}')
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/comunica_assenza', methods=['POST'])
@login_required
def comunica_assenza():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'message': 'ID turno non fornito'}), 400

        turno_id = data['id']
        turno = db.session.get(Turno, turno_id)
        
        if not turno:
            return jsonify({'success': False, 'message': 'Turno non trovato'}), 404
            
        # Verifica che l'utente stia comunicando l'assenza per un suo turno
        if turno.utenza_id != session.get('user_id'):
            return jsonify({'success': False, 'message': 'Non autorizzato'}), 403
            
        # Verifica che il turno non sia già passato
        if turno.data < datetime.now().date():
            return jsonify({'success': False, 'message': 'Non puoi comunicare assenza per un turno passato'}), 400
            
        # Verifica che non sia già stata comunicata un'assenza
        if db.session.query(Assenza).filter_by(turno_id=turno_id).first():
            return jsonify({'success': False, 'message': 'Assenza già comunicata per questo turno'}), 400

        # Crea la nuova assenza
        assenza = Assenza(
            turno_id=turno_id,
            data_comunicazione=datetime.now(),
            gestita=False
        )
        db.session.add(assenza)
        db.session.commit()

        # Invia email di notifica agli admin
        admin_users = db.session.query(Utenza).filter_by(tipo='admin').all()
        for admin in admin_users:
            email_template = f"""
            <h2>Nuova Comunicazione di Assenza</h2>
            <p>Un dipendente ha comunicato la sua assenza per un turno:</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; margin: 15px 0;">
                <p><strong>Dipendente:</strong> {turno.utenza.nome} {turno.utenza.cognome}</p>
                <p><strong>Data Turno:</strong> {turno.data.strftime('%d/%m/%Y')}</p>
                <p><strong>Turno:</strong> {turno.turno}</p>
                <p><strong>Tipo:</strong> {turno.tipo}</p>
                <p><strong>Data Comunicazione:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <p>È necessario gestire questa assenza il prima possibile.</p>
            
            <p style="text-align: center;">
                <a href="{url_for('gestisci_turni', _external=True)}" style="background-color: #4c1d95; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Gestisci Assenza
                </a>
            </p>
            """
            
            try:
                send_email(
                    admin.email,
                    "Il Boschetto - Nuova Comunicazione di Assenza",
                    email_template
                )
            except Exception as e:
                app.logger.error(f'Errore nell\'invio email ad admin {admin.email}: {str(e)}')

        return jsonify({'success': True, 'message': 'Assenza comunicata con successo'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nella comunicazione dell\'assenza: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Si è verificato un errore durante la comunicazione dell\'assenza'
        }), 500

@app.route('/check_assenze', methods=['GET'])
@login_required
def check_assenze():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({"success": False, "message": "Non autorizzato"}), 403
            
        # Trova tutte le assenze non gestite per turni futuri
        oggi = datetime.now().date()
        assenze = db.session.query(Assenza).join(Turno).filter(
            Assenza.gestita == False,
            Turno.data >= oggi
        ).all()
        
        if not assenze:
            return jsonify({"success": True, "assenze": []})
            
        result = []
        for assenza in assenze:
            turno = assenza.turno
            result.append({
                "id": assenza.id,
                "dipendente": f"{turno.utenza.nome} {turno.utenza.cognome}",
                "data": turno.data.strftime('%d/%m/%Y'),
                "turno_id": turno.id
            })
            
        return jsonify({"success": True, "assenze": result})
        
    except Exception as e:
        app.logger.error(f'Errore nel controllo delle assenze: {str(e)}')
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/marca_assenza_notificata', methods=['POST'])
@login_required
def marca_assenza_notificata():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({"success": False, "message": "Non autorizzato"}), 403
            
        data = request.get_json()
        assenza_id = data.get('id')
        
        assenza = db.session.get(Assenza, assenza_id)
        if not assenza:
            return jsonify({"success": False, "message": "Assenza non trovata"}), 404
            
        assenza.notificata = True
        db.session.commit()
        
        return jsonify({"success": True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nella marcatura dell\'assenza: {str(e)}')
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/modifica_utente', methods=['POST'])
@login_required
def modifica_utente():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({"success": False, "message": "Non autorizzato"}), 403

        utente_id = request.form.get('id')
        tipo = request.form.get('tipo')
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        email = request.form.get('email')

        if not all([utente_id, tipo, nome, cognome, email]):
            return jsonify({"success": False, "message": "Tutti i campi sono obbligatori"}), 400

        utente = db.session.get(Utenza, utente_id)
        if not utente:
            return jsonify({"success": False, "message": "Utente non trovato"}), 404

        # Controlla se l'email è già in uso da un altro utente
        existing_user = db.session.query(Utenza).filter(
            Utenza.email == email,
            Utenza.id != utente_id
        ).first()
        if existing_user:
            return jsonify({"success": False, "message": "Email già in uso da un altro utente"}), 400

        # Aggiorna i dati dell'utente
        utente.tipo = tipo
        utente.nome = nome
        utente.cognome = cognome
        utente.email = email

        db.session.commit()

        # Invia email di notifica
        email_template = f"""
        <h2>Notifica Modifica Account</h2>
        <p>Gentile {nome} {cognome},</p>
        <p>Ti informiamo che i tuoi dati sono stati modificati:</p>
        <ul>
            <li>Tipo account: {tipo}</li>
            <li>Nome: {nome}</li>
            <li>Cognome: {cognome}</li>
            <li>Email: {email}</li>
        </ul>
        <p>Se non hai richiesto questa modifica, contatta immediatamente il tuo supervisore.</p>
        """

        send_email(
            email,
            "Notifica Modifica Account - Il Boschetto",
            email_template
        )

        return jsonify({
            "success": True,
            "message": "Utente modificato con successo"
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nella modifica dell\'utente: {str(e)}')
        return jsonify({
            "success": False,
            "message": "Si è verificato un errore durante la modifica dell'utente"
        }), 500

@app.route('/recupera_password', methods=['POST'])
def recupera_password():
    try:
        # Verifica il CSRF token
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({'success': False, 'message': 'CSRF token mancante'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dati non forniti'}), 400

        email = data.get('email')
        if not email:
            return jsonify({'success': False, 'message': 'Email non fornita'}), 400
        
        utente = db.session.query(Utenza).filter_by(email=email).first()
        if not utente:
            return jsonify({'success': False, 'message': 'Email non trovata'}), 404
        
        # Genera una nuova password casuale
        password_originale = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Template per l'email di recupero password
        template_html = f"""
        <h2 style="color: #4c1d95; margin-bottom: 20px;">Recupero Credenziali</h2>
        <p>Gentile {utente.nome},</p>
        <p>Come richiesto, abbiamo generato delle nuove credenziali di accesso per il tuo account:</p>
        
        <div class="info-box">
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Nuova Password:</strong> {password_originale}</p>
        </div>
        
        <p>Per la tua sicurezza, ti consigliamo di:</p>
        <ul style="margin: 15px 0; padding-left: 20px;">
            <li>Cambiare la password al primo accesso</li>
            <li>Non condividere le tue credenziali con nessuno</li>
            <li>Utilizzare una password sicura e unica</li>
        </ul>
        
        <p style="color: #dc2626; margin-top: 20px;">Se non hai richiesto tu il recupero delle credenziali, contatta immediatamente il tuo supervisore.</p>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="{url_for('login', _external=True)}" class="button">
                Accedi al tuo account
            </a>
        </div>
        """
        
        try:
            # Invia l'email con il nuovo template
            send_email(
                email,
                'Il Boschetto - Recupero Credenziali',
                template_html
            )
        except Exception as e:
            app.logger.error(f'Errore nell\'invio email: {str(e)}')
            return jsonify({'success': False, 'message': 'Errore nell\'invio dell\'email'}), 500
        
        # Solo dopo aver inviato l'email con successo, salviamo la password hashata nel database
        try:
            utente.password = generate_password_hash(password_originale)
            db.session.commit()
        except Exception as e:
            app.logger.error(f'Errore nell\'aggiornamento della password: {str(e)}')
            return jsonify({'success': False, 'message': 'Errore nell\'aggiornamento della password'}), 500
        
        return jsonify({'success': True, 'message': 'Credenziali inviate via email'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nel recupero password: {str(e)}')
        return jsonify({'success': False, 'message': 'Errore durante l\'invio delle credenziali'}), 500

if __name__ == "__main__":
    test_smtp_connection()
    update_existing_passwords()
    app.run(debug=True,port=2001)
