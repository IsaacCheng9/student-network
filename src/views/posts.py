from urllib.parse import parse_qs
from urllib.parse import urlparse

from flask import Blueprint, render_template, redirect, jsonify

from src.helper import *

posts_blueprint = Blueprint("posts", __name__, static_folder="static",
                            template_folder="templates")


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
        cur.execute(
            "SELECT privacy, username "
            "FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchone()
        if row is None:
            return render_template("error.html",
                                   message=["This post does not exist."], )
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
                    return render_template("error.html", message=[
                        "This post is private. You cannot access it."], )
                else:
                    # Checks if user trying to view the post has a connection
                    # with the post author.
                    conn_type = get_connection_type(username)
                    if conn_type is not True:
                        if privacy == "protected":
                            return render_template(
                                "error.html",
                                message=["This post is only available to "
                                         "connections."])
                    else:
                        # If the user and author are connected, check that they
                        # are close friends.
                        connection = is_close_friend(username)
                        if connection is not True:
                            if privacy == "close":
                                return render_template(
                                    "error.html", message=[
                                        "This post is only available to close "
                                        "friends."])
        else:
            if privacy != "public":
                return render_template("error.html", message=[
                    "This post is private. You cannot access it."], )

        # Gets user from database using username.
        cur.execute(
            "SELECT title, body, username, date, account_type, likes, "
            "post_type FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchall()
        if len(row) == 0:
            message.append("This post does not exist.")
            message.append(
                "Please ensure you have entered the name correctly.")
            session["prev-page"] = request.url
            return render_template("error.html", message=message,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames())
        else:
            data = row[0]
            (title, body, username, date_posted,
             account_type, likes, post_type) = (data[0], data[1], data[2],
                                                data[3], data[4], data[5],
                                                data[6])

            # Check if user has liked post.
            cur.execute("SELECT username FROM UserLikes "
                        "WHERE postId=? AND username=?;",
                        (post_id, session["username"]))
            row = cur.fetchone()
            if row:
                liked = True
            else:
                liked = False

            cur.execute(
                "SELECT username FROM ACCOUNTS WHERE username=?;",
                (session["username"],))
            user_account_type = cur.fetchone()[0]

            if post_type in ("Image", "Link"):
                cur.execute(
                    "SELECT contentUrl "
                    "FROM PostContent WHERE postId=?;", (post_id,))
                content = cur.fetchone()
                if content is not None:
                    content = content[0]
            cur.execute(
                "SELECT *"
                "FROM Comments WHERE postId=?;", (post_id,))
            row = cur.fetchall()
            if len(row) == 0:
                session["prev-page"] = request.url
                return render_template(
                    "post_page.html", author=author, postId=post_id,
                    title=title, body=body, username=username,
                    date=date_posted, likes=likes, liked=liked,
                    account_type=account_type,
                    user_account_type=user_account_type,
                    comments=None, requestCount=get_connection_request_count(),
                    allUsernames=get_all_usernames(),
                    avatar=get_profile_picture(username), type=post_type,
                    content=content)
            for comment in row:
                time = datetime.strptime(
                    comment[3], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%y %H:%M")
                comments["comments"].append({
                    "commentId": comment[0],
                    "username": comment[1],
                    "body": comment[2],
                    "date": time,
                    "profilePic": get_profile_picture(comment[1])
                })
            session["prev-page"] = request.url
            return render_template(
                "post_page.html", author=author, postId=post_id,
                title=title, body=body, username=username,
                date=date_posted, likes=likes, accountType=account_type,
                user_account_type=user_account_type, comments=comments,
                requestCount=get_connection_request_count(),
                allUsernames=get_all_usernames(),
                avatar=get_profile_picture(username), type=post_type,
                content=content)


@posts_blueprint.route("/fetch_posts/", methods=['GET'])
def json_posts() -> dict:
    """
    Creates a JSON format for each post to make them readable by JavaScript.

    Returns:
        JSON dictionary file for posts.
    """
    number = request.args.get("number")
    starting_id = request.args.get("starting_id")
    all_posts, content, valid = fetch_posts(number, starting_id)
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

        connections = get_all_connections(session["username"])
        connections.append((session["username"],))
        cur.execute(
            "SELECT MAX(postId) FROM POSTS")
        row = cur.fetchone()

    all_posts, content, valid = fetch_posts(2, row[0])
    # Displays any error messages.

    all_posts = []

    if valid:
        if "error" in session:
            errors = session["error"]
            session.pop("error", None)
            session["prev-page"] = request.url
            return render_template("feed.html", posts=all_posts,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames(),
                                   errors=errors, content=content,
                                   max_id=row[0])
        else:
            session["prev-page"] = request.url
            return render_template("feed.html", posts=all_posts,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames(),
                                   content=content, max_id=row[0])
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
            (name_pattern, hobby_pattern, interest_pattern,))
        usernames = cur.fetchall()
        # Sorts results alphabetically.
        usernames.sort(key=lambda x: x[0])  # [(username, degree)]
        # Adds a profile picture to each user.
        usernames = list(map(lambda x: (
            x[0], x[1], x[2], get_profile_picture(x[0]), get_degree(x[0])[1]),
                             usernames))

    return jsonify(usernames)


@posts_blueprint.route("/submit_post", methods=["POST"])
def submit_post() -> object:
    """
    Submit post on social wall to database.

    Returns:
        Updated feed with new post added
    """
    valid = True
    form_type = request.form.get("form_type")
    post_privacy = request.form.get("privacy")

    if form_type == "Quiz":
        date_created, author, quiz_name, questions = save_quiz_details()
        valid, message = validate_quiz(quiz_name, questions)
        if valid:
            add_quiz(author, date_created, post_privacy, questions, quiz_name)
        else:
            session["error"] = message
            return redirect("quizzes")
    else:
        post_title = request.form["post_title"]
        post_body = request.form["post_text"]

        if form_type == "Image":
            file = request.files["file"]
            if not file:
                valid = False
            if valid:
                file_name_hashed = upload_image(file)
            elif file:
                valid = False

        elif form_type == "Link":
            link = request.form.get("link")
            if validate_youtube(link):
                data = urlparse(link)
                query = parse_qs(data.query)
                video_id = query["v"][0]
            else:
                valid = False

        # Only adds the post if a title has been input.
        if post_title != "" and valid is True:
            with sqlite3.connect("database.db") as conn:
                cur = conn.cursor()
                # Get account type
                cur.execute(
                    "SELECT type FROM ACCOUNTS "
                    "WHERE username=?;",
                    (session["username"],))
                account_type = cur.fetchone()[0]

                cur.execute(
                    "INSERT INTO POSTS (title, body, username, post_type, "
                    "privacy, account_type) VALUES (?, ?, ?, ?, ?, ?);",
                    (
                        post_title, post_body, session["username"],
                        form_type, post_privacy, account_type))
                conn.commit()

                if form_type == "Image" and valid is True:
                    cur.execute("INSERT INTO PostContent (postId, contentUrl) "
                                "VALUES (?, ?);",
                                (cur.lastrowid, "/static/images/post_imgs/" +
                                 file_name_hashed + ".jpg"))
                    conn.commit()
                elif form_type == "Link":
                    cur.execute("INSERT INTO PostContent (postId, contentUrl) "
                                "VALUES (?, ?);",
                                (cur.lastrowid, video_id))
                    conn.commit()

                update_submission_achievements(cur)
        else:
            # Prints error message stating that the title is missing.
            session["error"] = [
                "Make sure all fields are filled in correctly!"]

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
        # check user hasn't liked post already
        cur.execute("SELECT username, postId FROM UserLikes"
                    " WHERE postId=? AND username=? ;",
                    (post_id, session["username"]))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO UserLikes (postId,username)"
                        "VALUES (?, ?);", (post_id, session["username"]))

            # Gets number of current likes.
            cur.execute("SELECT likes, username FROM POSTS WHERE postId=?;",
                        (post_id,))
            row = cur.fetchone()
            likes = row[0] + 1
            username = row[1]

            cur.execute("UPDATE POSTS SET likes=? "
                        " WHERE postId=? ;", (likes, post_id,))
            conn.commit()

            cur.execute("SELECT username FROM AllUserLikes WHERE postId=?;",
                        (post_id,))
            row = cur.fetchall()
            names = [x[0] for x in row]
            print(row, names)
            if session["username"] not in names:
                # 1 exp earned for the author of the post
                check_level_exists(username, conn)
                cur.execute(
                    "UPDATE UserLevel "
                    "SET experience = experience + 1 "
                    "WHERE username=?;",
                    (username,))
                cur.execute("INSERT INTO AllUserLikes (postId,username)"
                            "VALUES (?, ?);", (post_id, session["username"]))
                conn.commit()

            update_post_achievements(cur, likes, username)
        else:
            # Gets number of current likes.
            cur.execute("SELECT likes FROM POSTS WHERE postId=?;",
                        (post_id,))
            row = cur.fetchone()
            likes = row[0] - 1

            cur.execute("UPDATE POSTS SET likes=? "
                        " WHERE postId=? ;", (likes, post_id,))
            conn.commit()

            cur.execute("DELETE FROM UserLikes "
                        "WHERE (postId=? AND username=?)",
                        (post_id, session["username"]))
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
            cur.execute("INSERT INTO Comments (postId, body, username) "
                        "VALUES (?, ?, ?);",
                        (post_id, comment_body, session["username"]))
            conn.commit()

            # Get username on post
            cur.execute(
                "SELECT username FROM POSTS "
                "WHERE postId=?;",
                (post_id,))
            username = cur.fetchone()[0]

            # Get number of comments
            cur.execute(
                "SELECT COUNT(commentId) FROM Comments "
                "WHERE postID=?;", (post_id,))
            row = cur.fetchone()[0]

            update_comment_achievements(row, username)

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
        cur.execute(
            "SELECT postId FROM POSTS WHERE postId=?;", (post_id,))
        row = cur.fetchone()
        # check the post exists in database
        if row[0] is None:
            message.append("Error: this post does not exist")
        else:
            cur.execute("DELETE FROM POSTS WHERE postId=?", (post_id,))
            conn.commit()

    message.append("Post has been deleted successfully.")
    session["prev-page"] = request.url
    return render_template("error.html", message=message,
                           requestCount=get_connection_request_count(),
                           allUsernames=get_all_usernames())


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
        cur.execute("SELECT * FROM Comments WHERE commentId=? ",
                    (comment_id,))
        row = cur.fetchone()
        # Checks that the comment exists.
        if row[0] is None:
            message.append("Comment does not exist.")
            session["prev-page"] = request.url
            return render_template("error.html", message=message,
                                   requestCount=get_connection_request_count(),
                                   allUsernames=get_all_usernames())
        else:
            cur.execute("DELETE FROM Comments WHERE commentId =? ",
                        (comment_id,))
            conn.commit()

    return redirect("post_page/" + post_id)