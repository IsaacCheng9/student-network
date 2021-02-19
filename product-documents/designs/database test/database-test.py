from flask import Flask, render_template, request

import boto3
import json

class Comment:
    def __init__(self, username, comment):
        self.username = username
        self.comment = comment


#client = boto3.client("dynamodb")
db = boto3.resource("dynamodb", "us-east-2")

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def home():
    return render_template("index.html",comments=ReadComments())

def ReadComments():
    table = db.Table("comments")

    response = table.scan()

    items = response["Items"]

    comments = []

    for item in items:
        newComment = Comment(item["username"], item["comment"])
        comments.append(newComment)

    return comments

ReadComments()
