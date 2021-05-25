"""
Performs checks and actions to help quizzes work effectively.
"""
import os
import sqlite3
from datetime import date
from random import sample
from typing import Tuple, List

from flask import request, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def add_quiz(author, date_created, questions, quiz_name):
    """
    Adds quiz to the database.

    Args:
        author: Person who created the quiz.
        date_created: Date the quiz was created (YYYY/MM/DD).
        questions: Questions and answers for the quiz.
        quiz_name: Name of the quiz.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Quiz (quiz_name, date_created, author,"
            "question_1, question_1_ans_1, question_1_ans_2,"
            "question_1_ans_3, question_1_ans_4, question_2,"
            "question_2_ans_1, question_2_ans_2, question_2_ans_3,"
            "question_2_ans_4, question_3, question_3_ans_1,"
            "question_3_ans_2, question_3_ans_3, question_3_ans_4,"
            "question_4, question_4_ans_1, question_4_ans_2,"
            "question_4_ans_3, question_4_ans_4, question_5,"
            "question_5_ans_1, question_5_ans_2, question_5_ans_3,"
            "question_5_ans_4) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                quiz_name,
                date_created,
                author,
                questions[0][0],
                questions[0][1],
                questions[0][2],
                questions[0][3],
                questions[0][4],
                questions[1][0],
                questions[1][1],
                questions[1][2],
                questions[1][3],
                questions[1][4],
                questions[2][0],
                questions[2][1],
                questions[2][2],
                questions[2][3],
                questions[2][4],
                questions[3][0],
                questions[3][1],
                questions[3][2],
                questions[3][3],
                questions[3][4],
                questions[4][0],
                questions[4][1],
                questions[4][2],
                questions[4][3],
                questions[4][4],
            ),
        )
        conn.commit()


def get_quiz_details(cur, quiz_id: int) -> Tuple[list, list, str, list, str]:
    """
    Gets the details for the quiz being taken.
    Args:
        cur: Cursor for the SQLite database.
        quiz_id: The ID of the quiz being taken.

    Returns:
        Answer options, questions, and author, details, and name of the quiz.
    """
    cur.execute("SELECT * FROM Quiz WHERE quiz_id=?;", (quiz_id,))
    quiz_details = cur.fetchone()
    quiz_name = quiz_details[1]
    quiz_author = quiz_details[3]
    question_1 = quiz_details[4]
    question_1_options = sample(
        [
            quiz_details[5],
            quiz_details[6],
            quiz_details[7],
            quiz_details[8],
        ],
        4,
    )
    question_2 = quiz_details[9]
    question_2_options = sample(
        [
            quiz_details[13],
            quiz_details[10],
            quiz_details[11],
            quiz_details[12],
        ],
        4,
    )
    question_3 = quiz_details[14]
    question_3_options = sample(
        [
            quiz_details[18],
            quiz_details[15],
            quiz_details[16],
            quiz_details[17],
        ],
        4,
    )
    question_4 = quiz_details[19]
    question_4_options = sample(
        [
            quiz_details[23],
            quiz_details[20],
            quiz_details[21],
            quiz_details[22],
        ],
        4,
    )
    question_5 = quiz_details[24]
    question_5_options = sample(
        [
            quiz_details[28],
            quiz_details[25],
            quiz_details[26],
            quiz_details[27],
        ],
        4,
    )
    # Gets a list of questions and answers to pass to the web page.
    questions = [question_1, question_2, question_3, question_4, question_5]
    answers = [
        question_1_options,
        question_2_options,
        question_3_options,
        question_4_options,
        question_5_options,
    ]
    return answers, questions, quiz_author, quiz_details, quiz_name


def save_quiz_details() -> Tuple[date, str, str, list]:
    """
    Gets details about questions and metadata for the quiz.

    Returns:
        Author, date created, questions, and quiz name.
    """
    # Gets quiz details.
    date_created = date.today()
    author = session["username"]
    quiz_name = request.form.get("quiz_name")
    questions = [
        [
            request.form.get("question_1"),
            request.form.get("question_1_ans_1"),
            request.form.get("question_1_ans_2"),
            request.form.get("question_1_ans_3"),
            request.form.get("question_1_ans_4"),
        ],
        [
            request.form.get("question_2"),
            request.form.get("question_2_ans_1"),
            request.form.get("question_2_ans_2"),
            request.form.get("question_2_ans_3"),
            request.form.get("question_2_ans_4"),
        ],
        [
            request.form.get("question_3"),
            request.form.get("question_3_ans_1"),
            request.form.get("question_3_ans_2"),
            request.form.get("question_3_ans_3"),
            request.form.get("question_3_ans_4"),
        ],
        [
            request.form.get("question_4"),
            request.form.get("question_4_ans_1"),
            request.form.get("question_4_ans_2"),
            request.form.get("question_4_ans_3"),
            request.form.get("question_4_ans_4"),
        ],
        [
            request.form.get("question_5"),
            request.form.get("question_5_ans_1"),
            request.form.get("question_5_ans_2"),
            request.form.get("question_5_ans_3"),
            request.form.get("question_5_ans_4"),
        ],
    ]
    return date_created, author, quiz_name, questions


def validate_quiz(quiz_name: str, questions: list) -> Tuple[bool, List[str]]:
    """
    Validates the quiz creation details which have been input by a user.

    Args:
        quiz_name: The name of the quiz input by the user.
        questions: The quiz question details input by the user.

    Returns:
        Whether the quiz is valid, and the error messages if not.
    """
    valid = True
    message = []

    # Checks that a quiz name has been made.
    if quiz_name.replace(" ", "") == "":
        valid = False
        message.append("You must enter a quiz name!")

    # Checks that all questions details have been filled in.
    for question in questions:
        for detail in question:
            if detail == "":
                valid = False
                message.append("You have not filled in details for all questions!")
                return valid, message

    return valid, message
