# Libs
from flask_wtf import FlaskForm
from wtforms import Form, validators, ValidationError
from wtforms.validators import DataRequired, Email
import email_validator
from wtforms import IntegerField, DateField, FloatField, HiddenField, TextAreaField, SubmitField, RadioField, SelectField, BooleanField, StringField, validators, PasswordField


# Form for the rent - transaction
class RentForm(FlaskForm):
    member = SelectField('Member who is renting a book', choices=[], coerce=int)
    book = SelectField('Book to rent', choices=[], coerce=int)
    action = SelectField("Status/Action", choices=(("rent", "rent"), ("returned", "returned"),("lost", "lost"),("None", "None")),default='rent')
    start_date = DateField('Start Date', format='%Y-%m-%d')
    end_date = DateField('End Date', format='%Y-%m-%d')
    submit = SubmitField('Submit')


# Form for accounting the payment
class PaymentForm(FlaskForm):
    member = SelectField('Member who is paying', choices=[], coerce=int)
   # action = SelectField("Status/Action", choices=(("debit", "debit"), ("credit", "credit"),("None", "None")),default='debit')
    value = FloatField("Amount $ paid")
    date = DateField('Date of Payment', format='%Y-%m-%d')
    submit = SubmitField('Submit')

# Form for updating a book
class ModifyBook(FlaskForm):
    book_id = HiddenField()
    book_title = StringField('Book title')
    authors = StringField('Authors')
    isbn = StringField('Isbn')
    num_pages = IntegerField('Number pages')
    publisher = StringField('Publisher')
    price = FloatField('Price for rent')
    submit = SubmitField('Submit')

# Form for creating a member
class Member(FlaskForm):
    name = StringField(label='Name', validators=[DataRequired()])
    email = StringField(label='Email', validators=[
    DataRequired(), Email(granular_message=True)])
    status = SelectField(choices=(("active", "active"), ("suspended", "suspended"),("None", "None")),default='active')
    submit = SubmitField(label="Submit")

