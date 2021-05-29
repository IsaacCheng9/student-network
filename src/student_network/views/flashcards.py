"""
Handles the view for flashcards and related functionality.
"""
import sqlite3

import student_network.helpers.helper_achievements as helper_achievements
import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_flashcards as helper_flashcards
from flask import Blueprint, json, redirect, render_template, request, session, jsonify


flashcards_blueprint = Blueprint(
    "flashcards", __name__, static_folder="static", template_folder="templates"
)


@flashcards_blueprint.route("/flashcards", methods=["GET"])
def flashcards() -> object:
    """
    Loads the sorted list of flashcards.

    Returns:
        The web page of flashcards.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT set_id, date_created, author, set_name, cards_played FROM QuestionSets"
        )
        row = cur.fetchall()
        set_posts = list(sorted(row, key=lambda x: x[4], reverse=True))
        set_posts = [list(x) for x in set_posts]

        for i, card_set in enumerate(set_posts):
            set_posts[i].append(helper_flashcards.get_question_count(cur, card_set[0]))

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template(
            "flashcards_view.html",
            requestCount=helper_connections.get_connection_request_count(),
            sets=set_posts,
            errors=errors,
            personal=False,
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )
    else:
        return render_template(
            "flashcards_view.html",
            requestCount=helper_connections.get_connection_request_count(),
            sets=set_posts,
            personal=False,
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )


@flashcards_blueprint.route("/flashcards/<username>", methods=["GET", "POST"])
def flashcards_user(username: str) -> object:
    """
    Loads specific user's flashcard data.

    Args:
        username: The username of the user to find sets from.

    Returns:
        The web page of flashcards created by this user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT set_id, date_created, author, set_name, cards_played "
            "FROM QuestionSets WHERE author=?;",
            (username,),
        )
        row = cur.fetchall()
        set_posts = sorted(row, key=lambda x: x[4], reverse=True)
        set_posts = [list(x) for x in set_posts]

        for i, card_set in enumerate(set_posts):
            set_posts[i].append(helper_flashcards.get_question_count(cur, card_set[0]))

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template(
            "flashcards_view.html",
            requestCount=helper_connections.get_connection_request_count(),
            sets=set_posts,
            errors=errors,
            personal=True,
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )
    else:
        return render_template(
            "flashcards_view.html",
            requestCount=helper_connections.get_connection_request_count(),
            sets=set_posts,
            personal=True,
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )


@flashcards_blueprint.route("/flashcards/edit/<set_id>", methods=["GET"])
def flashcards_edit(set_id: int) -> object:
    """
    Loads create new flashcard data.

    Args:
        set_id: The ID of the flashcards.

    Returns:
        The web page of flashcards created.
    """

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute("SELECT author FROM QuestionSets WHERE set_id=?;", (set_id,))
        author = cur.fetchone()[0]
        if author != session["username"]:
            return redirect("/flashcards/set/" + str(set_id))

        card_set = helper_flashcards.get_set_details(cur, set_id)

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template(
            "flashcards_edit.html",
            requestCount=helper_connections.get_connection_request_count(),
            questions=card_set[3],
            set_name=card_set[0],
            set_id=set_id,
            errors=errors,
            set_author=card_set[2],
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )
    else:
        return render_template(
            "flashcards_edit.html",
            requestCount=helper_connections.get_connection_request_count(),
            questions=card_set[3],
            set_name=card_set[0],
            set_id=set_id,
            set_author=card_set[2],
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )


@flashcards_blueprint.route("/flashcards/set/<set_id>", methods=["GET"])
def flashcard_set(set_id: int) -> object:
    """
    Loads the flashcard set.

    Args:
        set_id: The ID of the flashcards to load.

    Returns:
        The web page for answering the questions, or feedback for your answers.
    """

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        card_set = helper_flashcards.get_set_details(cur, set_id)

    # Displays any error messages.
    if "error" in session:
        errors = session["error"]
        session.pop("error", None)
        return render_template(
            "flashcards_set.html",
            requestCount=helper_connections.get_connection_request_count(),
            questions=card_set[3],
            set_name=card_set[0],
            set_id=set_id,
            errors=errors,
            set_author=card_set[2],
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )
    else:
        return render_template(
            "flashcards_set.html",
            requestCount=helper_connections.get_connection_request_count(),
            questions=card_set[3],
            set_name=card_set[0],
            set_id=set_id,
            set_author=card_set[2],
            username=session["username"],
            notifications=helper_general.get_notifications(),
        )


@flashcards_blueprint.route("/flashcards/new", methods=["GET", "POST"])
def flashcards_new() -> object:
    """
    Create a new flashcard set

    Returns:
        The web page of flashcards created.
    """

    set_id = helper_flashcards.generate_set()

    return redirect("/flashcards/edit/" + str(set_id))


@flashcards_blueprint.route("/flashcards/edit/add/<set_id>", methods=["GET", "POST"])
def flashcards_add(set_id) -> object:
    """
    Edit a specific set

    Args:
        set_id: The ID of the flashcards.

    Returns:
        The web page of flashcards set to edit.
    """

    helper_flashcards.add_card(set_id)

    return redirect("/flashcards/edit/" + str(set_id))


@flashcards_blueprint.route("/flashcards/delete/<set_id>", methods=["GET", "POST"])
def flashcards_delete(set_id) -> object:
    """
    Delete a flashcard set.

    Args:
        set_id: The ID of the flashcards.

    Returns:
        The web page of flashcards list.
    """

    helper_flashcards.delete_set(set_id)

    session["error"] = ["delete set"]

    return redirect("/flashcards")


@flashcards_blueprint.route("/flashcards/delete/<set_id>/<index>", methods=["GET"])
def flashcards_delete_question(set_id: int, index: str) -> object:
    """
    Delete a flashcard question.

    Args:
        set_id: The ID of the flashcards.

    Returns:
        The web page of flashcards list.
    """

    helper_flashcards.delete_question(set_id, int(index))

    return redirect("/flashcards/edit/" + str(set_id))


@flashcards_blueprint.route("/flashcards/save/<set_id>", methods=["GET", "POST"])
def flashcards_save(set_id) -> object:
    """
    Save the flashcard set

    Args:
        set_id: The ID of the flashcards.

    Returns:
        The web page of flashcards set.
    """

    helper_flashcards.save_set(set_id)

    session["error"] = ["save"]

    return redirect("/flashcards/edit/" + str(set_id))


@flashcards_blueprint.route("/flashcards/play/start/<set_id>", methods=["GET", "POST"])
def flashcards_start_set(set_id: int) -> object:
    """
    Starts the flashcard set to play and increments its play count

    Args:
        set_id: The ID of the flashcards.

    Returns:
        The web page for playing the flashcard set
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        helper_flashcards.add_play(cur, set_id)
        conn.commit()

    return redirect("/flashcards/play/" + str(set_id))


@flashcards_blueprint.route("/flashcards/play/<set_id>", methods=["GET", "POST"])
def flashcards_play(set_id: int) -> object:
    """
    Loads the flashcard set to play

    Args:
        set_id: The ID of the flashcards to load.

    Returns:
        The web page for playing the flashcard set
    """
    # Gets the flashcards details from the database.
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        (
            set_name,
            _,
            set_author,
            questions,
            plays,
        ) = helper_flashcards.get_set_details(cur, set_id)

        question_list = questions.items()

    helper_achievements.update_flashcard_achievements(set_author, plays)

    if request.method == "GET":
        return render_template(
            "flashcards_play.html",
            requestCount=helper_connections.get_connection_request_count(),
            set_name=set_name,
            set_id=set_id,
            # index=index,
            question_list=dict(question_list),
            question_count=len(question_list),
            set_author=set_author,
            notifications=helper_general.get_notifications(),
        )
