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


def get_set_details(cur, set_id: int) -> Tuple[str, date, str, dict, int]:
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

    if set_details[4]:
        questions = set_details[4].split("|")
    else:
        questions = ""
    if set_details[5]:
        answers = set_details[5].split("|")
    else:
        answers = ""
    questions_and_answers = {}
    for c, question in enumerate(questions):
        questions_and_answers[question] = answers[c]

    return (
        set_details[1],
        set_details[2],
        set_details[3],
        questions_and_answers,
        set_details[6],
    )


def delete_set(set_id):
    """
    Delete specific set

    Args:
        set_id: ID of the set to delete
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT author FROM QuestionSets WHERE set_id=?;", (set_id,))
        author = cur.fetchone()[0]
        if author == session["username"]:
            cur.execute("DELETE FROM QuestionSets WHERE set_id=?;", (set_id,))
            conn.commit()
        else:
            session["error"] = ["You cannot delete another user's flashcard set"]


def delete_question(set_id, index):
    """
    Delete specific set

    Args:
        set_id: ID of the set to delete from
        index: the index of the question to delete
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT author FROM QuestionSets WHERE set_id=?;", (set_id,))
        author = cur.fetchone()[0]
        if author == session["username"]:
            cur.execute(
                "SELECT questions, answers FROM QuestionSets WHERE set_id=?;", (set_id,)
            )
            set_details = cur.fetchone()
            if not all(set_details[0]):
                session["error"] = ["Question does not exist"]

            questions = set_details[0].split("|")
            answers = set_details[1].split("|")

            if len(questions) > index:
                questions.pop(index)
                questions = "|".join(questions)

                answers.pop(index)
                answers = "|".join(answers)
            else:
                session["error"] = ["Question does not exist"]

            cur.execute(
                "UPDATE QuestionSets SET questions=?, answers=? WHERE set_id=?;",
                (questions, answers, set_id),
            )
            conn.commit()

        else:
            session["error"] = ["You cannot delete another user's flashcard set"]


def save_set(set_id):
    """
    Save changes to question set

    Args:
        set_id: ID of the set to save
    """
    # Gets set details.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        count = get_question_count(cur, set_id)

    questions, answers = "", ""
    for i in range(count):
        new_q = str(request.form.get("question_" + str(i)))
        if new_q:
            new_q = validate_inputs(new_q)
            questions += new_q + "|"
        else:
            questions += "|"
        new_a = str(request.form.get("answer_" + str(i)))
        if new_a:
            new_a = validate_inputs(new_a)
            answers += new_a + "|"
        else:
            answers += "|"
    if questions:
        if questions[-1] == "|":
            questions = questions[:-1]
    if answers:
        if answers[-1] == "|":
            answers = answers[:-1]

    if request.form.get("set_name"):
        name = request.form.get("set_name")
    else:
        name = "Unnamed"

    cur.execute(
        "UPDATE QuestionSets SET set_name=?, questions=?, answers=? WHERE set_id=?;",
        (name, questions, answers, set_id),
    )
    conn.commit()


def generate_set() -> int:
    """
    Generate new set with logged in user as author

    Returns:
        set_id of new set
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO QuestionSets (date_created,author) VALUES (?, ?);",
            (date.today(), session["username"]),
        )
        cur.execute("SELECT MAX(set_id) FROM QuestionSets;")
        new_id = cur.fetchone()[0]

    return new_id


def add_card(set_id):
    """
    Add card to specific set

    Args:
        set_id: ID of the set to add to
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT questions, answers, author FROM QuestionSets WHERE set_id=?;",
            (set_id,),
        )
        row = cur.fetchone()

        author = row[2]
        if author == session["username"]:
            if all(row):
                question_list = row[0].split("|")
                answer_list = row[1].split("|")
                count = len(question_list) + 1
                if not "question " + str(count) in question_list:
                    questions = row[0] + "|question " + str(count)
                else:
                    q = "question " + str(count)
                    while q in question_list:
                        q = q + " 2"
                    questions = row[0] + "|" + q

                if not "answer " + str(count) in answer_list:
                    answers = row[1] + "|answer " + str(count)
                else:
                    a = "answer " + str(count)
                    while a in answer_list:
                        a = a + " 2"
                    answers = row[1] + "|" + a

            else:
                questions = "question1"
                answers = "answer1"

            cur.execute(
                "UPDATE QuestionSets SET questions=?, answers=? WHERE set_id=?;",
                (questions, answers, set_id),
            )
            conn.commit()

        else:
            session["error"] = ["You cannot add cards to another user's flashcard set"]


def add_play(cur, set_id):
    """
    Add 1 to plays for a set

    Args:
        set_id: ID of the set to increment
    """
    # Updates the number of times a quiz has been played.
    cur.execute(
        "UPDATE QuestionSets SET cards_played = cards_played + 1 WHERE set_id=?;",
        (set_id,),
    )


def get_question_count(cur, set_id) -> int:
    """
    Get number of questions in a set

    Args:
        set_id: ID of the set to count
    """
    cur.execute("SELECT questions FROM QuestionSets WHERE set_id=?;", (set_id,))
    set_details = cur.fetchone()
    if set_details[0] is None:
        return 0

    return len(set_details[0].split("|"))


def validate_inputs(text: str) -> str:
    """
    Cut the flashcard to max size of 600 characters and Remove '|' characters
    since they split questions in the database

    Args:
        text: input string

    Returns:
        Reformatted string
    """
    text = text[:600]
    return text.replace("|","")