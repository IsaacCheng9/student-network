from flask import Blueprint, render_template, redirect

from src.helper import *

quizzes_blueprint = Blueprint("quizzes", __name__, static_folder="static",
                              template_folder="templates")


@quizzes_blueprint.route("/quizzes", methods=["GET"])
def quizzes() -> object:
    """
    Loads the sorted list of quizzes.

    Returns:
        The web page of quizzes created.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT quiz_id, date_created, author, quiz_name, plays FROM Quiz")
        row = cur.fetchall()
        quiz_posts = sorted(row, key=lambda x: x[4], reverse=True)

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template("quizzes.html",
                               requestCount=get_connection_request_count(),
                               quizzes=quiz_posts, errors=errors)
    else:
        return render_template("quizzes.html",
                               requestCount=get_connection_request_count(),
                               quizzes=quiz_posts)


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
        (answers, questions, quiz_author,
         quiz_details, quiz_name) = get_quiz_details(cur, quiz_id)

    if request.method == "GET":
        return render_template("quiz.html",
                               requestCount=get_connection_request_count(),
                               quiz_name=quiz_name, quiz_id=quiz_id,
                               questions=questions, answers=answers,
                               quiz_author=quiz_author)
    elif request.method == "POST":
        score = 0
        # Gets the answers selected by the user.
        user_answers = [request.form.get("userAnswer0"),
                        request.form.get("userAnswer1"),
                        request.form.get("userAnswer2"),
                        request.form.get("userAnswer3"),
                        request.form.get("userAnswer4")]

        # Displays an error message if they have not answered all questions.
        if any(user_answers) == "":
            session["error"] = "You have not answered all the questions!"
            return redirect(session["prev-page"])
        else:
            # 1 exp earned for the author of the quiz
            if quiz_author != session["username"]:
                check_level_exists(quiz_author, conn)
                cur.execute(
                    "UPDATE UserLevel "
                    "SET experience = experience + 1 "
                    "WHERE username=?;",
                    (quiz_author,))
                conn.commit()
            question_feedback = []
            for i in range(5):
                correct_answer = quiz_details[0][(5 * i) + 5]
                correct = user_answers[i] == correct_answer
                question_feedback.append(
                    [questions[i], user_answers[i], correct_answer])
                if correct:
                    score += 1
            update_quiz_achievements(score)

            # Updates the number of times a quiz has been played.
            cur.execute("UPDATE Quiz SET plays = plays + 1 WHERE quiz_id=?;",
                        (quiz_id,))
            conn.commit()

            return render_template("quiz_results.html",
                                   question_feedback=question_feedback,
                                   requestCount=get_connection_request_count(),
                                   score=score)
