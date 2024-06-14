from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta
from forms import LoginForm, RegisterForm, EliminaUtenteForm, ModificaUtenteForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, template_folder='src', static_folder='src')
app.permanent_session_lifetime = timedelta(minutes=5)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Luigi2005@localhost:3306/gestioneturni_boschetto"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecret'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        utente = Utenza.query.filter_by(email=email).first()

        if utente and check_password_hash(utente.password, password):
            session['user_id'] = utente.id
            session.permanent = True
            flash('Login eseguito con successo!', 'success')

            if utente.tipo == 'admin':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('dashboard_user'))
        else:
            flash('Email o password non validi. Riprova.', 'danger')

    return render_template('login.html', form=form)

@app.route('/dashboardadmin')
def dashboard_admin():
    return render_template('dashboard_admin.html')

@app.route('/dashboarduser')
def dashboard_user():
    return render_template('dashboard_user.html')

@app.route('/turni', methods=['GET', 'POST'])
def gestisci_turni():
    if 'user_id' not in session:
        flash('Devi essere loggato per vedere questa pagina.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    utente = Utenza.query.get(user_id)
    
    if request.method == 'POST':
        data = request.form.get('data')
        turno = request.form.get('turno')
        tipo = request.form.get('tipo')

        if data and turno and tipo:
            nuovo_turno = Turno(data=datetime.strptime(data, '%Y-%m-%d'), turno=turno, tipo=tipo, utenza_id=user_id)
            db.session.add(nuovo_turno)
            db.session.commit()
            flash('Turno aggiunto con successo!', 'success')
        else:
            flash('Tutti i campi sono obbligatori.', 'danger')

    turni = Turno.query.filter_by(utenza_id=user_id).all()
    return render_template('gestisci_turni.html', turni=turni)

if __name__ == "__main__":
    app.run(debug=True)
