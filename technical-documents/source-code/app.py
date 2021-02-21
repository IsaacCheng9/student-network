from flask import Flask
from flask import request
from flask import render_template

APP = Flask(__name__)


@APP.route('/')
def home():
    return "Hello World!"

if __name__ == '__main__':
    APP.run()
