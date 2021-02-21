import requests
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'login_button' in request .form: 
            username = request.form['username_input']
            hashed_psw = request.form['psw_input']
        elif 'register_button' in request.form:
            username = request.form['username_input']
            psw = request.form['psw_input']
            psw_check = request.form['psw_input_check']

        