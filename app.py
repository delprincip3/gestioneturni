from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta
from forms import LoginForm, RegisterForm, EliminaUtenteForm, ModificaUtenteForm

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

        if utente and utente.password == password:
            session['user_id'] = utente.id
            session.permanent = True  # per mantenere la sessione permanente per la durata specificata
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

if __name__ == "__main__":
    app.run(debug=True)
