from flask import Flask
from flask import request
from flask import render_template

application = Flask(__name__)


@application.route('/')
def home():
    return render_template("test.html")

if __name__ == '__main__':
    application.debug=True
    application.run()
