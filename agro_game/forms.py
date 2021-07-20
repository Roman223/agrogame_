from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, BooleanField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.fields.html5 import DateField, DecimalRangeField
from agro_game.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя',
                           validators=[DataRequired(), Length(min=2, max=20)])
    registration_date = HiddenField()
    submit = SubmitField('Создать пользователя')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Имя пользователя занято.')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя',
                           validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class SessionInitForm(FlaskForm):
    # money = DecimalField('Стартовый капитал', places=2)
    difficulty = DecimalRangeField('Сложность', default=100)
    money = SelectField('Стартовый капитал', choices=[(100000000, 100000000)])
    session_start = DateField('Дата начала симуляции')
    submit = SubmitField('Инициализировать сессию')


class FieldBuyForm(FlaskForm):
    target_culture = SelectField('Целевая культура', coerce=str)
    purpose = SelectField('Назначение', choices=[('Корм', 'Кормовая цель'),
                                                 ('Продовольствие', 'Продовольственная цель')])
    prev_culture = SelectField('Предшественник', coerce=str)
    submit = SubmitField('Сформировать варианты')


# TODO: словарь для специализаций и заменить столбец в базе на столбец с номерами
class StuffForm(FlaskForm):
    qualification = SelectField('Квалификация', choices=[('1', 1),
                                                         ('2', 2)])
    specialization = SelectField('Специализация', choices=[('водитель', 'Водитель'),
                                                           ('тракторист', 'Тракторист'),
                                                           ('рабочий', 'Рабочий')]
                                 )

    payment = None

    submit = SubmitField('Нанять')


# shape = SelectField('Форма поля', choices=[('', 'Варианты')])
# soil_type = SelectField('Тип почвы', choices=[('', 'Варианты')])
# density = SelectField('Плотность')
# gran_sostav = None

class OperationForm(FlaskForm):
    operations = SelectField('Операция', coerce=str)
    machines = SelectMultipleField('СХМ')
    staff = SelectMultipleField('Персонал')
    submit = SubmitField('Готово')


class SeedForm(FlaskForm):
    quality = SelectField('Качество', choices=[('О', 'Оригинальные'),
                                               ('Э', 'Элитные'),
                                               ('РС', 'Репродукциннные для семенных целей'),
                                               ('Рст', 'Репродукционные для производства товарной продукции')]
                          )
    prices = {}
    submit = SubmitField('Купить')
