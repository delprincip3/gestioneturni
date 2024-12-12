from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
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
import requests
from sqlalchemy import or_

load_dotenv()  # Carica le variabili d'ambiente prima di configurare l'app

app = Flask(__name__, template_folder='src', static_folder='src')
app.permanent_session_lifetime = timedelta(minutes=5)
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
            utente = Utenza.query.get(utenza_id)
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
    
    # Paginazione
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(Turno.data.desc()).paginate(page=page, per_page=per_page, error_out=False)
    turni = pagination.items
    
    today = datetime.now().date()
    
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
                         utente_filter=utente_filter)

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
@login_required
def miei_turni():
    utente = Utenza.query.get(session['user_id'])
    turni = Turno.query.filter_by(utenza_id=utente.id).all()
    today = datetime.now().date()
    return render_template('miei_turni.html', utente=utente, turni=turni, today=today)

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

@app.route('/elimina_turno', methods=['POST'])
@login_required
def elimina_turno():
    try:
        data = request.get_json()
        turno_id = data.get('id')
        
        turno = Turno.query.get(turno_id)
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
        utente = Utenza.query.get(turno.utenza_id)
        
        # Prepara il template dell'email
        email_template = f"""
        <h2>Notifica Eliminazione Turno</h2>
        <p>Gentile {utente.nome} {utente.cognome},</p>
        <p>Ti informiamo che il tuo turno è stato eliminato:</p>
        <ul>
            <li>Data: {turno.data.strftime('%d/%m/%Y')}</li>
            <li>Turno: {turno.turno}</li>
            <li>Tipo: {turno.tipo}</li>
        </ul>
        <p>Se non hai richiesto questa modifica, contatta immediatamente il tuo supervisore.</p>
        """
        
        # Prima elimina l'assenza se esiste
        assenza = Assenza.query.filter_by(turno_id=turno_id).first()
        if assenza:
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
        
        turno = Turno.query.get(turno_id)
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
        vecchio_utente = Utenza.query.get(turno.utenza_id)
        nuovo_utente = Utenza.query.get(nuovo_utente_id)
        
        # Salva i vecchi dati per l'email
        vecchia_data = turno.data
        vecchio_turno_tipo = turno.turno
        vecchio_tipo = turno.tipo
        
        # Se c'è un'assenza associata, marcala come gestita
        assenza = Assenza.query.filter_by(turno_id=turno_id).first()
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
        turno_id = data.get('id')
        
        turno = Turno.query.get(turno_id)
        if not turno:
            return jsonify({"success": False, "message": "Turno non trovato"}), 404
            
        # Controlla se il turno è nel passato
        oggi = datetime.now().date()
        if turno.data < oggi:
            return jsonify({
                "success": False, 
                "message": "Non è possibile comunicare assenze per turni passati"
            }), 400
            
        # Controlla se esiste già una comunicazione di assenza
        if Assenza.query.filter_by(turno_id=turno_id).first():
            return jsonify({
                "success": False,
                "message": "Hai già comunicato l'assenza per questo turno"
            }), 400
            
        # Crea la nuova assenza
        assenza = Assenza(turno_id=turno_id)
        db.session.add(assenza)
        
        # Trova tutti gli admin
        admin_users = Utenza.query.filter_by(tipo='admin').all()
        
        # Invia email a tutti gli admin
        for admin in admin_users:
            email_template = f"""
            <h2>Comunicazione Assenza</h2>
            <p>Gentile {admin.nome} {admin.cognome},</p>
            <p>Il dipendente {turno.utenza.nome} {turno.utenza.cognome} ha comunicato la sua assenza per il seguente turno:</p>
            <ul>
                <li>Data: {turno.data.strftime('%d/%m/%Y')}</li>
                <li>Turno: {turno.turno}</li>
                <li>Tipo: {turno.tipo}</li>
            </ul>
            <p>Si consiglia di modificare o eliminare il turno.</p>
            """
            
            send_email(
                admin.email,
                f"Comunicazione Assenza - {turno.utenza.nome} {turno.utenza.cognome}",
                email_template
            )
        
        db.session.commit()
        return jsonify({"success": True, "message": "Assenza comunicata con successo"}), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Errore nella comunicazione dell\'assenza: {str(e)}')
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/check_assenze', methods=['GET'])
@login_required
def check_assenze():
    try:
        if session.get('user_type') != 'admin':
            return jsonify({"success": False, "message": "Non autorizzato"}), 403
            
        # Trova tutte le assenze non gestite per turni futuri
        oggi = datetime.now().date()
        assenze = Assenza.query.join(Turno).filter(
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
        
        assenza = Assenza.query.get(assenza_id)
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

        utente = Utenza.query.get(utente_id)
        if not utente:
            return jsonify({"success": False, "message": "Utente non trovato"}), 404

        # Controlla se l'email è già in uso da un altro utente
        existing_user = Utenza.query.filter(
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

if __name__ == "__main__":
    test_smtp_connection()
    update_existing_passwords()
    app.run(debug=True,port=2001)
