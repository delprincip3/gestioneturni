from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo,Optional

class RegisterForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[ ('User', 'User')], validators=[DataRequired()])
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