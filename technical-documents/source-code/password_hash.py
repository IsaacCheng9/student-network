# Flask connectivity required
'''
from flask import Flask, render_template, request
import html
app = Flask(__name__)
'''

import hashlib
import random

user_password = "myPassword123"

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
salt = ''.join(random.choice(ALPHABET) for i in range(16))

db_pw = user_password+salt

h = hashlib.md5(db_pw.encode())

print(user_password)
print(salt)
print(db_pw)
print(h.hexdigest())
