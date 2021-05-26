"""
Handles the view for quizzes and related functionality.
"""
import sqlite3

import student_network.helpers.helper_achievements as helper_achievements
import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_login as helper_login
import student_network.helpers.helper_quizzes as helper_quizzes
from flask import Blueprint, redirect, render_template, request, session

quizzes_blueprint = Blueprint(
    "quizzes", __name__, static_folder="static", template_folder="templates"
)


@quizzes_blueprint.route("/quizzes", methods=["GET"])
def quizzes() -> object:
    """
    Loads the sorted list of quizzes.

    Returns:
        The web page of quizzes created.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT quiz_id, date_created, author, quiz_name, plays FROM Quiz")
        row = cur.fetchall()
        quiz_posts = sorted(row, key=lambda x: x[4], reverse=True)

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template(
            "quizzes.html",
            requestCount=helper_connections.get_connection_request_count(),
            quizzes=quiz_posts,
            errors=errors,
            personal=False,
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )
    else:
        return render_template(
            "quizzes.html",
            requestCount=helper_connections.get_connection_request_count(),
            quizzes=quiz_posts,
            personal=False,
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )

@quizzes_blueprint.route("/quizzes/<username>", methods=["GET"])
def quizzes_user(username: str) -> object:
    """
    Loads the sorted list of quizzes.

    Returns:
        The web page of quizzes created.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT quiz_id, date_created, author, quiz_name, plays "
                    "FROM Quiz WHERE author=?;", (username,))
        row = cur.fetchall()
        quiz_posts = sorted(row, key=lambda x: x[4], reverse=True)

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template(
            "quizzes.html",
            requestCount=helper_connections.get_connection_request_count(),
            quizzes=quiz_posts,
            errors=errors,
            personal=True,
            username=username,
            notifications=helper_general.get_notifications(),
        )
    else:
        return render_template(
            "quizzes.html",
            requestCount=helper_connections.get_connection_request_count(),
            quizzes=quiz_posts,
            personal=True,
            username=username,
            notifications=helper_general.get_notifications(),
        )


@quizzes_blueprint.route("/quiz/<quiz_id>", methods=["GET", "POST"])
def quiz(quiz_id: int) -> object:
    """
    Loads the quiz and processes the user's answers.

    Args:
        quiz_id: The ID of the quiz to load.

    Returns:
        The web page for answering the questions, or feedback for your answers.
    """
    # Gets the quiz details from the database.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        (
            answers,
            questions,
            quiz_author,
            quiz_details,
            quiz_name,
        ) = helper_quizzes.get_quiz_details(cur, quiz_id)

    if request.method == "GET":
        return render_template(
            "quiz.html",
            requestCount=helper_connections.get_connection_request_count(),
            quiz_name=quiz_name,
            quiz_id=quiz_id,
            questions=questions,
            answers=answers,
            quiz_author=quiz_author,
            notifications=helper_general.get_notifications(),
        )
    elif request.method == "POST":
        score = 0
        # Gets the answers selected by the user.
        user_answers = [
            request.form.get("userAnswer0"),
            request.form.get("userAnswer1"),
            request.form.get("userAnswer2"),
            request.form.get("userAnswer3"),
            request.form.get("userAnswer4"),
        ]

        # Displays an error message if they have not answered all questions.
        if any(user_answers) == "":
            session["error"] = "You have not answered all the questions!"
            return redirect(session["prev-page"])
        else:
            # 1 exp earned for the author of the quiz
            if quiz_author != session["username"]:
                helper_login.check_level_exists(quiz_author, conn)
                helper_general.one_exp(cur, quiz_author)
                conn.commit()
            question_feedback = []
            for i in range(5):
                correct_answer = quiz_details[(5 * i) + 5]
                correct = user_answers[i] == correct_answer
                question_feedback.append(
                    [questions[i], user_answers[i], correct_answer]
                )
                if correct:
                    score += 1
            helper_achievements.update_quiz_achievements(score)

            # Updates the number of times a quiz has been played.
            cur.execute(
                "UPDATE Quiz SET plays = plays + 1 WHERE quiz_id=?;", (quiz_id,)
            )
            conn.commit()

            return render_template(
                "quiz_results.html",
                question_feedback=question_feedback,
                requestCount=helper_connections.get_connection_request_count(),
                score=score,
                notifications=helper_general.get_notifications(),
            )
