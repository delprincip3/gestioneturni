from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email

class RegisterForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('User', 'User')], validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    cognome = StringField('Cognome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Registrati')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EliminaUtenteForm(FlaskForm):
    submit = SubmitField('Elimina')

class ModificaUtenteForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('Admin', 'Admin'), ('User', 'User')], validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    cognome = StringField('Cognome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Salva')

class GestisciTurniForm(FlaskForm):
    data = DateField('Data', format='%Y-%m-%d', validators=[DataRequired()])
    turno = SelectField('Turno', choices=[('mattina', 'Mattina'), ('sera', 'Sera'), ('doppio turno', 'Doppio Turno')], validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('cameriere', 'Cameriere'), ('lavapiatti', 'Lavapiatti')], validators=[DataRequired()])
    utenza_id = SelectField('Utente', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Aggiungi Turno')
