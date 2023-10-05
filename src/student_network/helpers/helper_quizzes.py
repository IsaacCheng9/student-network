"""
Performs checks and actions to help quizzes work effectively.
"""
import os
import sqlite3
from datetime import date
from random import sample, choice
from typing import Tuple, List

from flask import request, session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")


def add_quiz(author, date_created, questions, answers, quiz_name):
    """
    Adds quiz to the database.

    Args:
        author: Person who created the quiz.
        date_created: Date the quiz was created (YYYY/MM/DD).
        questions: Questions for the quiz.
        answers: Answer options for the quiz.
        quiz_name: Name of the quiz.
    """
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        # Inserts the quiz details into the database.
        cur.execute(
            "INSERT INTO Quiz (quiz_name, date_created, author) VALUES (?, ?, ?);",
            (quiz_name, date_created, author),
        )
        # Gets the quiz ID of the quiz which has just been created.
        cur.execute(
            "SELECT MAX(quiz_id) FROM Quiz WHERE date_created=? AND author=? AND "
            "quiz_name=?",
            (
                date_created,
                author,
                quiz_name,
            ),
        )
        quiz_id = int(cur.fetchone()[0])
        # Inserts each question into the database.
        for question in range(len(questions)):
            cur.execute(
                "INSERT INTO Question (quiz_id, question, answer_1, answer_2, "
                "answer_3, answer_4) VALUES (?, ?, ?, ?, ?, ?);",
                (
                    quiz_id,
                    questions[question],
                    answers[question][0],
                    answers[question][1],
                    answers[question][2],
                    answers[question][3],
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
        Answer options, questions, author, details, and name of the quiz.
    """
    cur.execute("SELECT * FROM Quiz WHERE quiz_id=?;", (quiz_id,))
    quiz_details = cur.fetchone()
    quiz_name = quiz_details[1]
    quiz_author = quiz_details[3]
    # Gets a list of questions and answers to pass to the web page.
    cur.execute("SELECT * FROM Question WHERE quiz_id=?;", (quiz_id,))
    questions_raw = cur.fetchall()
    questions = []
    answers = []
    for question in questions_raw:
        questions.append(question[2])
        answers.append(
            sample(
                [question[3], question[4], question[5], question[6]],
                4,
            )
        )
    return answers, questions, quiz_author, quiz_details, quiz_name


def save_quiz_details() -> Tuple[date, str, str, list, list]:
    """
    Gets details about questions and metadata for the quiz.

    Returns:
        Date created, author, quiz name, questions, and answers.
    """
    # Gets quiz details.
    date_created = date.today()
    author = session["username"]
    quiz_name = request.form.get("quiz_name")
    # Gets a variable number of questions for the quiz.
    questions = []
    answers = []
    question = 1
    while True:
        if request.form.get("question_" + str(question)):
            questions.append(request.form.get("question_" + str(question)))
            answers.append(
                [
                    request.form.get("question_" + str(question) + "_ans_1"),
                    request.form.get("question_" + str(question) + "_ans_2"),
                    request.form.get("question_" + str(question) + "_ans_3"),
                    request.form.get("question_" + str(question) + "_ans_4"),
                ]
            )
            question += 1
        else:
            break
    return date_created, author, quiz_name, questions, answers


def generate_answers_from_set(set_id):
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM QuestionSets WHERE set_id=?;", (set_id,))
        set_details = cur.fetchone()

        if set_details:
            if set_details[4]:
                questions = set_details[4].split("|")
            else:
                questions = []
            if set_details[5]:
                answers = set_details[5].split("|")
            else:
                answers = []
        else:
            questions, answers = [], []

        mc_answers = [[x] for x in answers]
        for i, answer in enumerate(mc_answers):
            for _ in range(3):
                add = answer[0]
                count = 0
                while add in answer and count < len(answers):
                    add = choice(answers)
                    count += 1
                mc_answers[i].append(add)

        return (set_details[2], set_details[3], set_details[1], questions, mc_answers)


def validate_quiz(
    quiz_name: str, questions: list, answers: list
) -> Tuple[bool, List[str]]:
    """
    Validates the quiz creation details which have been input by a user.

    Args:
        quiz_name: The name of the quiz input by the user.
        questions: The questions input by the user.
        answers: The answers for each question input by the user.

    Returns:
        Whether the quiz is valid, and the error messages if not.
    """
    valid = True
    message = []
    # Checks that a quiz name has been made.
    if quiz_name.replace(" ", "") == "":
        valid = False
        message.append("You must enter a quiz name!")
    # Checks that at least one question has been entered.
    if len(questions) == 0:
        valid = False
        message.append("You must enter at least one question!")
    # Checks that all question details have been filled in.
    for question in questions:
        if question == "":
            valid = False
            message.append("You have entered an empty question!")
    for answer in answers:
        for option in answer:
            if option == "":
                valid = False
                message.append(
                    "You have not entered four answer options for each question!"
                )

    return valid, message


def make_quiz(
    quiz_name: str, questions: list, answers: list, author: str, date_created: date
):
    valid, message = validate_quiz(quiz_name, questions, answers)
    print(valid, message, quiz_name, questions, answers)
    if valid:
        add_quiz(author, date_created, questions, answers, quiz_name)
        # Redirect the user to the quiz they just created.
        with sqlite3.connect("db.sqlite3") as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT MAX(quiz_id) FROM Quiz WHERE date_created=? AND author=? AND "
                "quiz_name=?",
                (
                    date_created,
                    author,
                    quiz_name,
                ),
            )
            quiz_id = str(cur.fetchone()[0])
        return quiz_id
    else:
        session["error"] = message
        return False


def delete_quiz(quiz_id):
    """
    Delete specific quiz

    Args:
        quiz_id: ID of the quiz to delete
    """
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        cur.execute("SELECT author FROM Quiz WHERE quiz_id=?;", (quiz_id,))
        author = cur.fetchone()[0]
        if author == session["username"]:
            cur.execute("DELETE FROM Question WHERE quiz_id=?;", (quiz_id,))
            conn.commit()
            cur.execute("DELETE FROM Quiz WHERE quiz_id=?;", (quiz_id,))
            conn.commit()
        else:
            session["error"] = ["You cannot delete another user's quiz"]


def get_question_count(cur, quiz_id):
    """
    Get number of questions in a quiz

    Args:
        quiz_id: ID of the quiz to count
    """
    cur.execute("SELECT question FROM Question WHERE quiz_id=?;", (quiz_id,))
    set_details = cur.fetchall()

    if set_details[0] is None:
        return 0

    return len(set_details)


def get_user_quizzes(username: str) -> list:
    """
    Get the quizzes of a given user

    Args:
        username: username to get quizzes from

    Returns:
        list of quizzes belonging to the user
    """
    with sqlite3.connect("db.sqlite3") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT quiz_id, date_created, author, quiz_name, plays "
            "FROM Quiz WHERE author=?;",
            (username,),
        )
        row = cur.fetchall()
        quiz_posts = sorted(row, key=lambda x: x[4], reverse=True)
        quiz_posts = [list(x) for x in quiz_posts]

        for i, quiz in enumerate(quiz_posts):
            quiz_posts[i].append(get_question_count(cur, quiz[0]))

    return quiz_posts
