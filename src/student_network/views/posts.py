"""
Handles the view for posts on the feed and related functionality.
"""

import re
import sqlite3
from datetime import datetime

import student_network.helpers.helper_achievements as helper_achievements
import student_network.helpers.helper_connections as helper_connections
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_login as helper_login
import student_network.helpers.helper_posts as helper_posts
import student_network.helpers.helper_profile as helper_profile
from flask import Blueprint, jsonify, redirect, render_template, request, session

posts_blueprint = Blueprint(
    "posts", __name__, static_folder="static", template_folder="templates"
)


@posts_blueprint.route("/post_page/<post_id>", methods=["GET"])
def post(post_id: int) -> object:
    """
    Loads a post and comments on that post.

    Returns:
        Redirection to the post page.
    """
    comments = {"comments": []}
    message = []
    author = ""
    session["prev-page"] = request.url
    content = None
    # check post restrictions
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT privacy, username FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchone()
        if row is None:
            return render_template(
                "error.html",
                message=["This post does not exist."],
                requestCount=helper_connections.get_connection_request_count(),
            )
        privacy = row[0]
        username = row[1]
        # check its if its an anonymous user or a logged in user
        if "username" not in session:
            return redirect("/login")
        if session.get("username"):
            # check if the user is the same as the author of the post
            if username != session["username"]:
                # check if post is available for display
                if privacy == "private":
                    return render_template(
                        "error.html",
                        message=["This post is private. You cannot access it."],
                    )
                else:
                    # Checks if user trying to view the post has a connection
                    # with the post author.
                    conn_type = helper_connections.get_connection_type(username)
                    if conn_type is not True:
                        if privacy == "protected":
                            return render_template(
                                "error.html",
                                message=["This post is only available to connections."],
                            )
                    else:
                        # If the user and author are connected, check that they
                        # are close friends.
                        connection = helper_connections.is_close_friend(
                            session["username"], username
                        )
                        if connection is not True:
                            if privacy == "close":
                                return render_template(
                                    "error.html",
                                    message=[
                                        "This post is only available to close "
                                        "friends."
                                    ],
                                )
        else:
            if privacy != "public":
                return render_template(
                    "error.html",
                    message=["This post is private. You cannot access it."],
                )

        # Gets user from database using username.
        cur.execute(
            "SELECT body, username, date, likes " "FROM POSTS WHERE postId=?;",
            (post_id,),
        )
        row = cur.fetchall()
        if len(row) == 0:
            message.append("This post does not exist.")
            message.append("Please ensure you have entered the name correctly.")
            session["prev-page"] = request.url
            return render_template(
                "error.html",
                message=message,
                requestCount=helper_connections.get_connection_request_count(),
                allUsernames=helper_general.get_all_usernames(),
                notifications=helper_general.get_notifications(),
            )
        else:
            data = row[0]
            (body, username, date_posted, account_type, likes) = (
                data[0],
                data[1],
                data[2],
                helper_posts.get_account_type(data[1]),
                data[3],
            )

            liked = helper_posts.check_if_liked(cur, post_id, session["username"])

            cur.execute(
                "SELECT username FROM ACCOUNTS WHERE username=?;",
                (session["username"],),
            )
            user_account_type = cur.fetchone()[0]

            cur.execute(
                "SELECT contentUrl from PostContent WHERE postId=?;", (post_id,)
            )
            images = cur.fetchall()

            cur.execute("SELECT *" "FROM Comments WHERE postId=?;", (post_id,))
            row = cur.fetchall()
            if len(row) == 0:
                session["prev-page"] = request.url
                return render_template(
                    "post_page.html",
                    author=author,
                    postId=post_id,
                    body=body,
                    username=username,
                    date=date_posted,
                    likes=likes,
                    liked=liked,
                    images=images,
                    account_type=account_type,
                    user_account_type=user_account_type,
                    comments=None,
                    requestCount=helper_connections.get_connection_request_count(),
                    allUsernames=helper_general.get_all_usernames(),
                    avatar=helper_profile.get_profile_picture(username),
                    content=content,
                    notifications=helper_general.get_notifications(),
                )
            for comment in row:
                time = datetime.strptime(comment[3], "%Y-%m-%d %H:%M:%S")
                comments["comments"].append(
                    {
                        "commentId": comment[0],
                        "username": comment[1],
                        "body": comment[2],
                        "date": helper_general.display_short_notification_age(
                            (datetime.now() - time).total_seconds()
                        ),
                        "profilePic": helper_profile.get_profile_picture(comment[1]),
                    }
                )
            session["prev-page"] = request.url
            return render_template(
                "post_page.html",
                author=author,
                postId=post_id,
                body=body,
                username=username,
                liked=liked,
                date=date_posted,
                likes=likes,
                images=images,
                account_type=account_type,
                user_account_type=user_account_type,
                comments=comments,
                requestCount=helper_connections.get_connection_request_count(),
                allUsernames=helper_general.get_all_usernames(),
                avatar=helper_profile.get_profile_picture(username),
                content=content,
                notifications=helper_general.get_notifications(),
            )


@posts_blueprint.route("/fetch_posts/", methods=["GET"])
def json_posts() -> dict:
    """
    Creates a JSON format for each post to make them readable by JavaScript.

    Returns:
        JSON dictionary file for posts.
    """
    number = request.args.get("number")
    starting_id = request.args.get("starting_id")
    all_posts, _, _ = helper_posts.fetch_posts(number, starting_id)
    return jsonify(all_posts)


@posts_blueprint.route("/feed", methods=["GET"])
def feed() -> object:
    """
    Checks user is logged in before viewing their feed page.

    Returns:
        Redirection to their feed if they're logged in.
    """
    session["prev-page"] = request.url
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        connections = helper_general.get_all_connections(session["username"])
        connections.append((session["username"],))
        cur.execute("SELECT MAX(postId) FROM POSTS")
        row = cur.fetchone()

    _, content, valid = helper_posts.fetch_posts(2, row[0])
    # Displays any error messages.
    if valid:
        if "error" in session:
            errors = session["error"]
            session.pop("error", None)
            session["prev-page"] = request.url
            return render_template(
                "feed.html",
                requestCount=helper_connections.get_connection_request_count(),
                allUsernames=helper_general.get_all_usernames(),
                errors=errors,
                content=content,
                max_id=row[0],
                notifications=helper_general.get_notifications(),
            )
        else:
            session["prev-page"] = request.url
            return render_template(
                "feed.html",
                requestCount=helper_connections.get_connection_request_count(),
                allUsernames=helper_general.get_all_usernames(),
                content=content,
                max_id=row[0],
                notifications=helper_general.get_notifications(),
            )
    else:
        return redirect("/login")


@posts_blueprint.route("/search_query", methods=["GET"])
def search_query() -> dict:
    """
    Searches for members registered in the student network.

    Returns:
        JSON dictionary of search results of users, and their hobbies
        and interests.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        chars = request.args.get("chars")
        hobby = request.args.get("hobby")
        interest = request.args.get("interest")
        name_pattern = "%" + chars + "%"
        hobby_pattern = "%" + hobby + "%"
        interest_pattern = "%" + interest + "%"

        # Filters by username, common hobbies, and interests.
        cur.execute(
            "SELECT UserProfile.username, UserHobby.hobby, "
            "UserInterests.interest FROM UserProfile "
            "LEFT JOIN UserHobby ON UserHobby.username=UserProfile.username "
            "LEFT JOIN UserInterests ON "
            "UserInterests.username=UserProfile.username "
            "WHERE (UserProfile.username LIKE ?) "
            "AND (IFNULL(hobby, '') LIKE ?) AND (IFNULL(interest, '') LIKE ?) "
            "GROUP BY UserProfile.username LIMIT 10;",
            (
                name_pattern,
                hobby_pattern,
                interest_pattern,
            ),
        )
        usernames = cur.fetchall()
        # Sorts results alphabetically.
        usernames.sort(key=lambda x: x[0])  # [(username, degree)]
        # Adds a profile picture to each user.
        usernames = list(
            map(
                lambda x: (
                    x[0],
                    x[1],
                    x[2],
                    helper_profile.get_profile_picture(x[0]),
                    helper_profile.get_degree(x[0])[1],
                ),
                usernames,
            )
        )

    return jsonify(usernames)


@posts_blueprint.route("/submit_post", methods=["POST"])
def submit_post() -> object:
    """
    Submit post on social wall to database.

    Returns:
        Updated feed with new post added
    """
    post_privacy = request.form.get("privacy")
    post_body = request.form["post_text"]
    all_file_names = request.form["allFileNames"].split(",")

    # Only adds the post if a title has been input.
    if len(all_file_names) > 0 or len(post_body) > 0:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            # Get account type
            cur.execute(
                "SELECT type FROM ACCOUNTS WHERE username=?;",
                (session["username"],),
            )
            cur.execute("SELECT COUNT(*) FROM POSTS")
            row_count = int(cur.fetchone()[0])
            row_id = row_count + 1
            cur.execute(
                "INSERT INTO POSTS (postId, body, username,"
                "privacy) VALUES (?, ?, ?, ?);",
                (
                    row_id,
                    post_body,
                    session["username"],
                    post_privacy,
                ),
            )

            if len(all_file_names) > 0:
                for fileName in all_file_names:
                    cur.execute(
                        "INSERT INTO PostContent (postId, contentUrl) "
                        "VALUES (?, ?);",
                        (
                            row_id,
                            fileName,
                        ),
                    )

            conn.commit()
            usernames_tagged = re.findall(r"@(\w+)", post_body)
            for username in usernames_tagged:
                helper_general.new_notification_username(
                    username,
                    "You have been tagged by {} in a post!".format(session["username"]),
                    "/post_page/{}".format(row_id),
                )
            helper_posts.update_submission_achievements(cur)
    else:
        # Prints error message stating that the title is missing.
        session["error"] = ["Make sure all fields are filled in correctly!"]

    return redirect("/feed")


@posts_blueprint.route("/like_post", methods=["POST"])
def like_post() -> object:
    """
    Processes liking a post to the database.

    Returns:
        Redirection to the post with like added.
    """
    post_id = request.form["postId"]

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        liked = helper_posts.check_if_liked(cur, post_id, session["username"])
        if not liked:
            cur.execute(
                "INSERT INTO UserLikes (postId,username) VALUES (?, ?);",
                (post_id, session["username"]),
            )

            # Gets number of current likes.
            cur.execute("SELECT likes, username FROM POSTS WHERE postId=?;", (post_id,))
            row = cur.fetchone()
            likes = row[0] + 1
            username = row[1]

            cur.execute(
                "UPDATE POSTS SET likes=? WHERE postId=? ;",
                (
                    likes,
                    post_id,
                ),
            )
            conn.commit()

            cur.execute("SELECT username FROM AllUserLikes WHERE postId=?;", (post_id,))
            row = cur.fetchall()
            names = [x[0] for x in row]
            if session["username"] not in names:
                # 1 exp earned for the author of the post
                helper_login.check_level_exists(username, conn)
                cur.execute(
                    "UPDATE UserLevel "
                    "SET experience = experience + 1 "
                    "WHERE username=?;",
                    (username,),
                )
                cur.execute(
                    "INSERT INTO AllUserLikes (postId,username) VALUES (?, ?);",
                    (post_id, session["username"]),
                )
                conn.commit()

            helper_achievements.update_post_achievements(cur, likes, username)
        else:
            # Gets number of current likes.
            cur.execute("SELECT likes FROM POSTS WHERE postId=?;", (post_id,))
            row = cur.fetchone()
            likes = row[0] - 1

            cur.execute(
                "UPDATE POSTS SET likes=? WHERE postId=? ;",
                (
                    likes,
                    post_id,
                ),
            )
            conn.commit()

            cur.execute(
                "DELETE FROM UserLikes WHERE (postId=? AND username=?)",
                (post_id, session["username"]),
            )
            conn.commit()

    return redirect("/post_page/" + post_id)


@posts_blueprint.route("/submit_comment", methods=["POST"])
def submit_comment() -> object:
    """
    Submit comment on post page to database.

    Returns:
        Updated post with new comment added
    """
    post_id = request.form["postId"]
    comment_body = request.form["comment_text"]

    # Only submits the comment if it is not empty.
    if comment_body.replace(" ", "") != "":
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Comments (postId, body, username) VALUES (?, ?, ?);",
                (post_id, comment_body, session["username"]),
            )
            conn.commit()

            # Get username on post
            cur.execute("SELECT username FROM POSTS WHERE postId=?;", (post_id,))
            username = cur.fetchone()[0]

            # Get number of comments
            cur.execute(
                "SELECT COUNT(commentId) FROM Comments WHERE postID=?;", (post_id,)
            )
            row = cur.fetchone()[0]

            helper_posts.update_comment_achievements(row, username)

            # we haven't commented on our own post
            if username != session["username"]:
                helper_general.new_notification_username(
                    username,
                    "{} has commented on your post!".format(session["username"]),
                    "/post_page/{}".format(post_id),
                )

    session["postId"] = post_id
    return redirect("/post_page/" + post_id)


@posts_blueprint.route("/delete_post", methods=["POST"])
def delete_post() -> object:
    """
    Deletes a post from the database.

    Returns:
        Renders a page stating that the post has been deleted successfully.
    """
    post_id = request.form["postId"]
    message = []

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT postId FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchone()
        # check the post exists in database
        if row[0] is None:
            message.append("Error: this post does not exist")
        else:
            cur.execute(
                "UPDATE POSTS SET privacy=? WHERE postId=?;", ("deleted", post_id)
            )
            conn.commit()

    message.append("Post has been deleted successfully.")
    session["prev-page"] = request.url
    return render_template(
        "error.html",
        message=message,
        requestCount=helper_connections.get_connection_request_count(),
        allUsernames=helper_general.get_all_usernames(),
        notifications=helper_general.get_notifications(),
    )


@posts_blueprint.route("/delete_comment", methods=["POST"])
def delete_comment() -> object:
    """
    Deletes a comment from the database.

    Returns:
        Redirection to the post page.
    """
    message = []
    post_id = request.form["postId"]
    comment_id = request.form["commentId"]

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Comments WHERE commentId=? ", (comment_id,))
        row = cur.fetchone()
        # Checks that the comment exists.
        if row[0] is None:
            message.append("Comment does not exist.")
            session["prev-page"] = request.url
            return render_template(
                "error.html",
                message=message,
                requestCount=helper_connections.get_connection_request_count(),
                allUsernames=helper_general.get_all_usernames(),
                notifications=helper_general.get_notifications(),
            )
        else:
            cur.execute("DELETE FROM Comments WHERE commentId =? ", (comment_id,))
            conn.commit()

    return redirect("post_page/" + post_id)


@posts_blueprint.route("/upload_file", methods=["POST"])
def upload_file():
    """
    An API that sends the files using a form, they are then saved here
    and a list of names of the files is returned
    """
    max_file_upload = 10
    file_names = []
    if request.files:
        for file_name in request.files:
            file = request.files[file_name]

            file_name = helper_posts.upload_image(file)
            file_names.append(file_name)

            max_file_upload -= 1
            if max_file_upload <= 0:
                break

    return jsonify(file_names)


@posts_blueprint.route("/delete_file", methods=["POST"])
def delete_file():
    """
    An API call to delete a file with a given name from the server
    """
    file_name = request.args.get("filename")
    # try and prevent escaping this path
    file_name.replace(".", "")
    file_name.replace("/", "")
    helper_posts.delete_file(file_name + ".jpg")
    return "200"

@posts_blueprint.route("/user_exists", methods=["GET"])
def user_exists():
    username = request.args.get("username")

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        cur.execute("SELECT username FROM ACCOUNTS WHERE username=?;", (username,))

        row = cur.fetchone()

        if row is None:
            return "False"

        return "True"

    return "False"

