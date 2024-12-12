from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField,HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[
        ('admin', 'Admin'),
        ('user', 'User')
    ], validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    cognome = StringField('Cognome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Registrati')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    class Meta:
        csrf = True  # Abilita protezione CSRF

class ModificaUtenteForm(FlaskForm):
    id = HiddenField('ID')
    tipo = SelectField('Tipo Utente', choices=[('admin', 'Admin'), ('user', 'User')], validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired()])
    cognome = StringField('Cognome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Salva Modifiche')

class EliminaUtenteForm(FlaskForm):
    id = HiddenField('ID')
    submit = SubmitField('Elimina')
class GestisciTurniForm(FlaskForm):
    data = DateField('Data', format='%Y-%m-%d', validators=[DataRequired()])
    turno = SelectField('Turno', choices=[('mattina', 'Mattina'), ('sera', 'Sera'), ('doppio turno', 'Doppio Turno')], validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[('cameriere', 'Cameriere'), ('lavapiatti', 'Lavapiatti')], validators=[DataRequired()])
    utenza_id = SelectField('Utente', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Aggiungi Turno')

class CambiaPasswordForm(FlaskForm):
    password_attuale = PasswordField('Password Attuale', validators=[DataRequired()])
    nuova_password = PasswordField('Nuova Password', validators=[
        DataRequired(),
        Length(min=8, message='La password deve essere di almeno 8 caratteri')
    ])
    conferma_password = PasswordField('Conferma Password', validators=[
        DataRequired(),
        EqualTo('nuova_password', message='Le password devono coincidere')
    ])
    submit = SubmitField('Cambia Password')
