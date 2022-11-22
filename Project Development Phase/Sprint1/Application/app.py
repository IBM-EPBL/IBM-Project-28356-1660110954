from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from authlib.integrations.flask_client import OAuth
def send_simple_message(msg,email):
    sender_address = 'healthyharvest.ibm@gmail.com'
    sender_pass = 'nlsqdmlhkbrooouy'
    receiver_address = email
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = email
    message['Subject'] = 'Greetings from Healthy Harvest'   
    message.attach(MIMEText(msg, 'plain'))
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls() 
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()

app = Flask(__name__)

app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'ibm'
app.config.from_object('config')

oauth = OAuth(app)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/login', methods =['GET', 'POST'])
def login():
    if (session):
        print(session)
        return render_template('home.html', activeTab = "home")
    msg = ''
    if request.method == 'POST' and 'loginEmail' in request.form and 'loginPassword' in request.form:
        email = request.form['loginEmail']
        password = request.form['loginPassword']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = % s AND password = % s', (email, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['email'] = account['email']
            return render_template('home.html', activeTab = "home")
        else:
            msg = 'Incorrect username / password !'
    return render_template('authentication.html', msg = msg)

@app.route('/logout')
def logout():
    session.clear()
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('email', None)
    return redirect(url_for('home'))

@app.route('/login_using_google')
def login_using_google():
    redirect_uri = url_for('auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    email = token['userinfo']['email']
    password = token['userinfo']['sub']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM accounts WHERE email = % s', (email, ))
    account = cursor.fetchone()
    if account:
        msg = 'Account already exists !'
    else:
        username = token['userinfo']['name']
        cursor.execute('Create Table `'+email+'`(id int primary key auto_increment,state varchar(100),district varchar(100),crop_year int,season varchar(50),crop varchar(100),area double,production double)')
        mysql.connection.commit()
        cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
        mysql.connection.commit()
        cursor.execute('SELECT * FROM accounts WHERE email = % s AND password = % s', (email, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['email'] = account['email']
        msg = '''
Hi '''+username+''',

We can’t wait for you to start using our product and seeing results in your business.

Please feel free to get started and learn more about how to use Healthy Harvest.

As always, our support team can be reached at healthyharvest.ibm@gmail.com if you ever get stuck.

Have a great day!'''
        send_simple_message(msg,email)
        return render_template('home.html', activeTab = "home")
    return render_template('authentication.html', msg = msg)

@app.route('/signup', methods = ['POST','GET'])
def signup():
    if (request.method=='GET'):
        return render_template('welcome.html')
    if (session):
        return render_template('home.html', activeTab = "home")
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        else:
            cursor.execute('Create Table `'+email+'`(id int primary key auto_increment,state varchar(100),district varchar(100),crop_year int,season varchar(50),crop varchar(100),area double,production double)')
            mysql.connection.commit()
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            cursor.execute('SELECT * FROM accounts WHERE email = % s AND password = % s', (email, password, ))
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['email'] = account['email']
            msg = '''
Hi '''+username+''',

We can’t wait for you to start using our product and seeing results in your business.

Please feel free to get started and learn more about how to use Healthy Harvest.

As always, our support team can be reached at healthyharvest.ibm@gmail.com if you ever get stuck.

Have a great day!'''
            send_simple_message(msg,email)
            return render_template('home.html', activeTab = "home")
    return render_template('authentication.html', msg = msg)

if __name__ == '__main__':
  app.run(debug=True)
