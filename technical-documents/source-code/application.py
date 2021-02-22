from flask import Flask, render_template, request, redirect, session
from passlib.hash import sha256_crypt
import sqlite3

application = Flask(__name__)
application.secret_key = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'

@application.route('/', methods=['GET'])
def index_page():
    return redirect("/login")


@application.route('/login', methods=['GET'])
def login_page():
    errors = []
    if 'error' in session:
        errors = session['error']
    session.pop('error', None)
    return render_template('login.html', errors=errors)


@application.route('/login', methods=['POST'])
def login_submit():
    username = request.form['username_input']
    psw = request.form['psw_input']
    # Get user from database using username
    # Compare password with hashed password
    # Compare using sha256_crypt.verify(psw, hashed_password)
    return redirect("/postpage")


@application.route('/error', methods=['GET'])
def errortest():
    session['error'] = ['login']
    return redirect("/login")

@application.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')


@application.route('/register', methods=['POST'])
def register_submit():
    try:
        username = request.form['username_input']
        email = request.form['email_input']
        psw = request.form['psw_input']
        psw_check = request.form['psw_input_check']
        if password_check(psw, psw_check):
            print('Password Matches')
            hash_psw = sha256_crypt.hash(psw)
            with sqlite3.connect('database.db') as conn
                cur = conn.cursor()
                cur.execute("INSERT INTO ACCOUNTS (username,password,email,type) VALUES (?,?,?,?);",(username,hash_psw,email,'student',))
                conn.commit()
                conn.close()
        else:
            print('Passwords do not match')
            session['error'] = ['passwordMatch']
            return redirect("/register")
    except:
        con.rollback()
    finally:
        return redirect("/postpage")


@application.route('/postpage', methods=['GET'])
def post_page():
    return render_template('postpage.html')


def password_check(psw, psw_check):
    if psw == psw_check:
        return True
    else:
        return False


if __name__ == '__main__':
    application.run(debug=True)


#print("password1 -> " + password)
#print("password2 -> " + password2)

#print(sha256_crypt.verify("myPassword123", password))
#print(sha256_crypt.verify("myPassword1234", password))
