from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import Yuzer, dbSession

class RegistrForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')
    def validateUsername(self, username):
        sessia = dbSession()
        yuzer = sessia.query(Yuzer).filter(Yuzer.name == username.data).first()
        if yuzer: raise ValidationError('Такое имя уже занято.')
    def validateEmail(self, email):
        sessia = dbSession()
        yuzer = sessia.query(Yuzer).filter(Yuzer.email == email.data).first()
        if yuzer: raise ValidationError('Этот email уже используется.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    rememberMe = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class StatyaForm(FlaskForm):
    zagolovok = StringField('Заголовок', validators=[DataRequired()])
    soderzhanie = TextAreaField('Содержание', validators=[DataRequired()])
    category = SelectMultipleField('Категории', coerce=int)
    submit = SubmitField('Сохранить')

class CountryForm(FlaskForm):
    nazvanie = StringField('Название', validators=[DataRequired()])
    teg = StringField('Тег (три буквы)', validators=[DataRequired()])
    ideologiya = StringField('Идеология')
    istoricheskayaSpravka = TextAreaField('Историческая справка')
    flagFileName = StringField('Имя файла флага')
    category = SelectMultipleField('Категории', coerce=int)
    submit = SubmitField('Сохранить')

class MechanicForm(FlaskForm):
    nazvanie = StringField('Название', validators=[DataRequired()])
    opisanie = TextAreaField('Описание', validators=[DataRequired()])
    category = SelectMultipleField('Категории', coerce=int)
    submit = SubmitField('Сохранить')

class UnitForm(FlaskForm):
    nazvanie = StringField('Название', validators=[DataRequired()])
    tip = StringField('Тип')
    ataka = IntegerField('Атака', default=0)
    zashita = IntegerField('Защита', default=0)
    skorost = IntegerField('Скорость', default=0)
    opisanie = TextAreaField('Описание')
    category = SelectMultipleField('Категории', coerce=int)
    submit = SubmitField('Сохранить')

class TechnologyForm(FlaskForm):
    nazvanie = StringField('Название', validators=[DataRequired()])
    opisanie = TextAreaField('Описание')
    era = StringField('Эра')
    category = SelectMultipleField('Категории', coerce=int)
    submit = SubmitField('Сохранить')

class NationalFocusForm(FlaskForm):
    nazvanie = StringField('Название', validators=[DataRequired()])
    opisanie = TextAreaField('Описание')
    stranaTeg = StringField('Тег страны')
    category = SelectMultipleField('Категории', coerce=int)
    submit = SubmitField('Сохранить')

class CommentForm(FlaskForm):
    text = TextAreaField('Комментарий', validators=[DataRequired()])
    submit = SubmitField('Отправить')