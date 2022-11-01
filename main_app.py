# Libraries
import os
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, VARCHAR, ForeignKey, DATE, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import requests
import datetime
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from src.forms import PaymentForm, RentForm, ModifyBook, Member
from flask_paginate import Pagination, get_page_parameter


# DB Connections
print (os.getcwd())
pth = os.getcwd()
engine = create_engine(f"sqlite:///{pth}/data/books.db",echo=True,connect_args={"check_same_thread": False})
conn = engine.connect()
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
meta = MetaData ()

## DB init
members_tbl= Table(
    'members_tbl',meta,
    Column('member_id', Integer, primary_key=True),
    Column('member_name', String),
    Column('member_email', String),
    Column('member_status', String),
)

books_tbl  = Table(
    'books_tbl', meta,
    Column('books_id',Integer,primary_key=True),
    Column('title',String),
    Column('authors',String),
    Column('isbn',String),
    Column('num_pages',Integer),
    Column('publisher',String),
    Column('price_pday',Float)
)

transactions_tbl= Table(
    'transactions_tbl',meta,
    Column('tx_id', Integer, primary_key=True),
    Column('books_id', Integer, ForeignKey("books_tbl.books_id")),
    Column('member_id', Integer, ForeignKey("members_tbl.member_id")),
    Column('Action',String),
    Column('tx_date', DateTime),
    Column('start_date', DateTime),
    Column('end_date', DateTime),
    Column('due_amount',Float),

)

payments_tbl = Table (
    'payments_tbl',meta,
    Column('payment_id', Integer, primary_key=True),
    Column('tx_id', Integer, ForeignKey("transactions_tbl.tx_id")),
    Column('member_id', Integer, ForeignKey("members_tbl.member_id")),
    Column('payment_amount',Float),
    Column('date_paid', DateTime, onupdate=datetime.datetime.now()),
    Column('action',String),
)

## Important in the first initializing of the app
meta.create_all(engine)
### END DB


# Path and APP init
module_path = os.path.dirname(os.path.abspath(__file__))
print (os.getcwd())
app = Flask(__name__)
os.chdir(os.path.dirname(__file__))
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config["DEBUG"] = True

# Define secret key to enable session
app.secret_key = 'biblioteca2022'


@app.route ("/init")
def init():
    """
    Endpoint for initializing and populate the DB
    Only use when you start the app the first time
    """

    def jsoncreator ():
        url = 'https://frappe.io/api/method/frappe-library'
        response = requests.get(url)
        data = response.json()
        jsondata = data["message"]
        return jsondata

    
    def initialize (jsondata):
        for e in jsondata:

                ins = books_tbl.insert().values(
                books_id=e["bookID"],
                title=e["title"],
                authors = e["authors"].encode('utf-8'),
                isbn = e["isbn"],
                num_pages = e ["  num_pages"],
                publisher = e ["publisher"],
                )
                session.execute(ins)

        return True

    jsondata = jsoncreator ()
    result = initialize(jsondata)
    if result:
        print ("Everything ok")


    return redirect(url_for('/'))





# Start the app and landing on dashboard/index page
@app.route("/")
def main():
    """Function for rendering the main page an dashboard"""

    query1 = f'SELECT Count(member_id) FROM members_tbl'
    members = session.execute(query1).fetchone()
    query2 = f'SELECT SUM(payment_amount) From payments_tbl'
    cash = session.execute(query2).fetchone()
    query3 = f'SELECT SUM(due_amount) From transactions_tbl'
    turnover = session.execute(query3).fetchone()

    return render_template('index.html', members=members[0], cash=cash[0], turnover=(turnover[0])*-1)



# Live Search in the Dashboard page
@app.route("/ajaxlivesearch",methods=["POST","GET"])
def ajaxlivesearch():
    """Function for receiving the data from the ajax live search"""
    
    if request.method == 'POST':
        search_word = request.form['querys']
        print(search_word)
        if search_word == '':
            query = f'SELECT * FROM books_tbl ORDER BY books_id'
            book = session.execute(query).fetchall()
        else:    
            query = f"SELECT * FROM books_tbl WHERE title LIKE '%{search_word}%' OR authors LIKE '%{search_word}%' OR publisher LIKE '%{search_word}%' OR isbn LIKE '%{search_word}%' ORDER BY books_id DESC LIMIT 20"
            book = session.execute(query).fetchall()
         
    return jsonify({'htmlresponse': render_template('response.html', book=book)})



# Realize a new rent (simplified)
@app.route("/orders", methods=["GET", "POST"])
def orders():
    """Function for doing a book rent transaction, use the price per day to calculate the complete price for the rent"""

    form = RentForm()
    bk = books_tbl.select()
    result = session.execute(bk).fetchall()
    book_list=[(i.books_id, i.title) for i in result]
    form.book.choices = book_list
    mb = members_tbl.select()
    result = session.execute(mb).fetchall()
    member_list=[(j.member_id, j.member_name) for j in result]
    form.member.choices = member_list

    if form.validate_on_submit():
        print(f"member_id:{form.member.data}, book_id:{form.book.data}, start: {form.start_date.data},  end:{form.end_date.data}")      
        query = f'Select price_pday FROM books_tbl WHERE books_id = {form.book.data}'
        price = session.execute(query).fetchone()
        days = (form.end_date.data - form.start_date.data).total_seconds()/3600/24
        due_amount = (price[0]*days)*-1
        ins = transactions_tbl.insert().values(books_id=form.book.data,member_id=form.member.data, Action=form.action.data, tx_date=datetime.datetime.now(), start_date = form.start_date.data, end_date = form.end_date.data,due_amount=due_amount )       
        session.execute(ins)
        session.commit()
        flash(f" Book rent: member_id:{form.member.data}, book_id:{form.book.data}, start: {form.start_date.data},  end:{form.end_date.data} " ,'success')
        return redirect(url_for('orders'))

    
    return render_template('order_form.html', msg="Register renting", title="Register renting", form=form)




# Adding new member
@app.route("/members", methods=["GET", "POST"])
def members():
    """Function for creating new members, CREATE"""

    cform = Member()
    if cform.validate_on_submit():
        ins = members_tbl.insert().values(member_name=cform.name.data,member_email=cform.email.data,member_status=cform.status.data)
        result = session.execute(ins)
        session.commit()
        flash('Member created','success')
        return redirect(url_for('members'))

    else:
        per_page = 10
        page = request.args.get(get_page_parameter(), type=int, default=1)
        offsets = (page - 1) * per_page
        print(page)
        mb = session.query(members_tbl).limit(10).offset(offsets)
        result = session.query(members_tbl).count()
        pagination = Pagination(page=page,per_page=per_page,offset=offsets, total=result,record_name=" members")
        pass

    return render_template('new_member.html', msg="Add new members", title="Add new members", form=cform, result=mb, pagination=pagination,)



# Accounting payment
@app.route("/payments",methods=["GET", "POST"])
def payments():
    """Function for visualization of clients' debts and accounting of payments"""
    

    ## Calculates the payments vs. the transactions costs
    query = f"""
    select member_id,member_name, sum(Saldo) as open_to_pay from
    (SELECT members_tbl.member_name, members_tbl.member_id, SUM(transactions_tbl.due_amount) As Saldo
    FROM members_tbl
    LEFT JOIN transactions_tbl ON transactions_tbl.member_id = members_tbl.member_id
    GROUP By members_tbl.member_name, members_tbl.member_id

    UNION 

    SELECT members_tbl.member_name, members_tbl.member_id, SUM(payments_tbl.payment_amount) As Saldo
    FROM members_tbl
    LEFT JOIN payments_tbl ON payments_tbl.member_id = members_tbl.member_id
    GROUP By members_tbl.member_name,members_tbl.member_id) group by member_name, member_id
    """

    dues = session.execute(query).fetchall()
    print (dues)

    # Preparing the form for render
    form = PaymentForm()
    mb = members_tbl.select()
    result = session.execute(mb).fetchall()
    member_list=[(j.member_id, j.member_name) for j in result]
    form.member.choices = member_list


    if form.validate_on_submit():
        print(f"member_id:{form.member.data}, value:{form.value.data}, paid_date: {form.date.data}")      
        ins = payments_tbl.insert().values(member_id=form.member.data, payment_amount = form.value.data, date_paid =form.date.data  )       
        session.execute(ins)
        session.commit()
        flash(f" Payment booked: member_id:{form.member.data}, value:{form.value.data}, paid_date: {form.date.data}" ,'success')
        return redirect(url_for('payments'))

    return render_template('payments.html', result=dues, msg="Register payments", title="Register payments", form=form)



# Stock
@app.route("/stock", methods = ['GET'])
def stock():
    """Function for rendering the book stock overview with pagination"""

    per_page = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offsets = (page - 1) * per_page
    print(page)
    wk = session.query(books_tbl).limit(10).offset(offsets)
    result = session.query(books_tbl).count()

    pagination = Pagination(page=page,per_page=per_page,offset=offsets, total=result,record_name=" books")
    return render_template('stock.html', result=wk, pagination=pagination,)



# Update book
@app.route('/modify_book/<id>', methods=['POST', 'GET'])
def modify_book(id):
    """Function for preparing and populating the updateForm in order to update a choosen book"""
    form_mb = ModifyBook()

    # data for prepopulate form with original data
    data = session.execute(books_tbl.select().where(books_tbl.columns.books_id == id)).fetchall()
    mod_data = {}
    mod_data["book_id"] = data[0][0]
    mod_data["book_title"] = data[0][1]
    mod_data["authors"] = data[0][2]
    mod_data["isbn"] = data[0][3]
    mod_data["num_pages"] = data[0][4]
    mod_data["publisher"] = data[0][5]
    mod_data["price"] = data[0][6]

    # data and form to render
    return render_template('modify_form.html', msg="Modify books", title="Modify books",form=form_mb, datas=mod_data)


# Action updating book
@app.route('/update_book', methods=['GET', 'POST'])
def update_book():
    """Function for updating a book"""

    form_upd = ModifyBook()
    if form_upd.validate_on_submit():
        for key, value in request.form.items():
            print(key, '->', value)
        
        upd = books_tbl.update().where(books_tbl.columns.books_id == form_upd.book_id.data).values(
            title=form_upd.book_title.data, authors = form_upd.authors.data, 
            isbn = form_upd.isbn.data , num_pages = form_upd.num_pages.data ,
            publisher = form_upd.publisher.data,
            price_pday= form_upd.price.data
            )
        result = session.execute(upd)
        session.commit()
        flash(f" Book successfuly updates: book_id:{form_upd.book_id.data}, book_title:{form_upd.book_title.data}, " ,'success')
        mod_data = {}
        mod_data["book_id"] = form_upd.book_id.data
        mod_data["book_title"] = form_upd.book_title.data
        mod_data["authors"] = form_upd.authors.data
        mod_data["isbn"] = form_upd.isbn.data
        mod_data["num_pages"] = form_upd.num_pages.data
        mod_data["publisher"] = form_upd.publisher.data
        mod_data["price"] = form_upd.price.data

    else:
        pass

    return render_template('modify_form.html', msg="Modify books", title="Modify books",form=form_upd, datas=mod_data)



if __name__ == "__main__":
    app.run()