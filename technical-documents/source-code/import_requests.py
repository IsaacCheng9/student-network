import requests
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'login_button' in request.form: 
            username = request.form['username_input']
            hashed_psw = request.form['psw_input']
        elif 'register_button' in request.form:
            username = request.form['username_input']
            psw = request.form['psw_input']
            psw_check = request.form['psw_input_check']
            if password_check(psw, psw_check):
                print('Password Matches')
            else:
                print('Passwords do not match')


def password_check(psw, psw_check):
    if psw == psw_check:
        return True
    else:
        return False      