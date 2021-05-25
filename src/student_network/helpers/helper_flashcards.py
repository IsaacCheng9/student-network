"""
Performs checks and actions to help flashcard sets work effectively.
"""
import os
import sqlite3
from datetime import date
from typing import Tuple, List

from flask import request, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def add_card_set(author, date_created, post_privacy, questions, set_name, answers): ###
    """
    Adds flashcard set to the database.

    Args:
        author: Person who created the flashcard set.
        date_created: Date the flashcard set was created (YYYY/MM/DD).
        post_privacy: Privacy setting for the flashcard set.
        questions: Questions and answers for the flashcard set.
        set_name: Name of the flashcard set.
    """
    questions = "|".join(questions)
    answers = "|".join(answers)
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO QuestionSets (set_name, date_created, author,"
            "questions, answers, privacy) "
            "VALUES (?, ?, ?, ?, ?, ?);",
            (
                set_name,
                date_created,
                author,
                questions,
                answers,
                post_privacy,
            ),
        )
        conn.commit()


def get_set_details(cur, set_id: int) -> Tuple[str, date, dict, int]:
    """
    Gets the details for the flashcard set being used.
    Args:
        cur: Cursor for the SQLite database.
        set_id: The ID of the flashcard set being used.

    Returns:
        Questions with answers, author, and name of the set.
    """
    cur.execute("SELECT * FROM QuestionSets WHERE set_id=?;", (set_id,))
    set_details = cur.fetchone()
    #set_id = set_details[0]
    #set_name = set_details[1]

    #set_author = set_details[3]
    if set_details[4]:
        questions = set_details[4].split("|")
    else: questions = ""
    if set_details[5]:
        answers = set_details[5].split("|")
    else: answers = ""
    questions_and_answers = {}
    for c, question in enumerate(questions):
        questions_and_answers[question] = answers[c]

    #return set_name, set_author, questions_and_answers
    return set_details[1], set_details[2], set_details[3], questions_and_answers, set_details[6]

def delete_set(set_id):

    print(set_id)

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM QuestionSets "
                    "WHERE set_id=?;",
                    (set_id,))
        conn.commit()

'''
def save_set_question() -> Tuple[date, str, str, list]:     #####
    """
    Gets details about questions and metadata for the set.

    Returns:
        Author, date created, questions, answers, and set name.
    """
    # Gets set details.
    date_created = date.today()
    author = session["username"]
    set_name = request.form.get("set_name")
    question = request.form.get("question")
    answer = request.form.get("answer")

    return date_created, author, set_name, question, answer
'''

def generate_set():

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO QuestionSets (date_created,author) "
                    "VALUES (?, ?);",
                    (date.today(), session["username"]))
        cur.execute("SELECT MAX(set_id) FROM QuestionSets;")
        new_id = cur.fetchone()[0]

    return new_id

def save_set(set_id):           #####

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO QuestionSets (date_created,author,questions,"
                    "answers) "
                    "VALUES (?, ?, "", "");",
                    (date.today(), session["username"]))
        cur.execute("SELECT MAX(set_id) FROM QuestionSets;")
        new_id = cur.fetchone()[0]

def add_card(set_id):

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT questions, answers "
                    "FROM QuestionSets "
                    "WHERE set_id=?;", (set_id,))
        row = cur.fetchone()
        print(row)
        count = len(row[0].split("|"))
        questions = row[0] + "|question "+str(count)
        answers= row[1] + "|answer "+str(count)
        print(questions, answers)
        cur.execute("UPDATE QuestionSets "
                    "SET questions=?, answers=? "
                    "WHERE set_id=?;",
                    (questions, answers, set_id))
        conn.commit()

