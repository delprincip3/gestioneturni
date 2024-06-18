from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta
from forms import LoginForm, RegisterForm, EliminaUtenteForm, ModificaUtenteForm, GestisciTurniForm

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

        if utente and utente.password == password:
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

@app.route('/gestisci_utenti', methods=['GET', 'POST'])
def gestisci_utenti():
    if 'user_id' not in session:
        flash('Devi essere loggato per vedere questa pagina.', 'danger')
        return redirect(url_for('login'))

    modifica_form = ModificaUtenteForm()
    elimina_form = EliminaUtenteForm()

    if request.method == 'POST':
        if 'modifica_submit' in request.form and modifica_form.validate_on_submit():
            utente_id = request.form.get('id')
            utente = Utenza.query.get(utente_id)
            if utente:
                utente.tipo = modifica_form.tipo.data
                utente.nome = modifica_form.nome.data
                utente.cognome = modifica_form.cognome.data
                utente.email = modifica_form.email.data
                utente.password = modifica_form.password.data
                db.session.commit()
                flash('Utente modificato con successo!', 'success')

        elif 'elimina_submit' in request.form and elimina_form.validate_on_submit():
            utente_id = request.form.get('id')
            utente = Utenza.query.get(utente_id)
            if utente:
                Turno.query.filter_by(utenza_id=utente_id).delete()
                db.session.delete(utente)
                db.session.commit()
                flash('Utente eliminato con successo!', 'success')

        return redirect(url_for('gestisci_utenti'))

    utenti = Utenza.query.all()
    return render_template('gestisci_utenti.html', modifica_form=modifica_form, elimina_form=elimina_form, utenti=utenti)



if __name__ == "__main__":
    app.run(debug=True)
