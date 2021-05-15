"""
Performs checks and actions to help the post system work effectively.
"""
import os
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Tuple

from PIL import Image
from flask import request, session
from student_network.helper_achievements import apply_achievement
from student_network.helper_general import allowed_file, get_all_connections
from student_network.helper_profile import get_profile_picture
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def check_if_liked(cur, post_id: int, username: str) -> bool:
    """
    Checks if the given user has liked the post.

    Args:
        cur: Cursor for the SQLite database.
        post_id: ID of the post to check
        username: username to check if post is liked from

    Returns:
        True if post has been liked by user, False if not
    """
    cur.execute("SELECT username FROM UserLikes "
                "WHERE postId=? AND username=?;",
                (post_id, username))
    if cur.fetchone():
        return True
    return False


def fetch_posts(number: int, starting_id: int) -> Tuple[dict, str, bool]:
    """
    Fetches posts which are visible by the user logged in.

    Args:
        number: Number of posts.
        starting_id: ID of the first post to fetch, in descending order.

    Returns:
        A dictionary of details in the post, type of post, and validity of
        post.
    """
    content = ""
    all_posts = {
        "AllPosts": []
    }
    if "username" in session:
        session["prev-page"] = request.url
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()

            connections = get_all_connections(session["username"])
            connections.append((session["username"],))
            row = []
            for user in connections:
                cur.execute(
                    "SELECT * FROM POSTS "
                    "WHERE username=? AND postId <= ?"
                    "AND privacy!='private' AND privacy!='close' "
                    "ORDER BY postId DESC LIMIT ?;",
                    (user[0], starting_id, number))
                row += cur.fetchall()
            # Sort reverse chronologically
            row = sorted(row, key=lambda x: x[0], reverse=True)
            i = 0

            # account type differentiation in posts db
            for user_post in row:
                if i == int(number):
                    break
                add = ""
                if len(user_post[2]) > 250:
                    add = "..."
                time = datetime.strptime(user_post[4], '%Y-%m-%d').strftime(
                    '%d-%m-%y')

                # Get account type
                cur.execute("SELECT type "
                            "FROM ACCOUNTS WHERE username=? ",
                            (user_post[3],))

                accounts = cur.fetchone()
                account_type = accounts[0]

                post_id = user_post[0]
                post_type = user_post[8]

                cur.execute("SELECT * FROM Comments WHERE postId=? LIMIT 5;",
                            (post_id,))
                comments = cur.fetchall()

                comments = list(map(lambda x: (x[0], x[1], x[2], x[3], x[4],
                                               get_profile_picture(x[1])),
                                    comments))

                if post_type in ("Image", "Link"):
                    cur.execute(
                        "SELECT contentUrl "
                        "FROM PostContent WHERE postId=?;", (post_id,))

                    content = cur.fetchone()
                    if content is not None:
                        content = content[0]

                cur.execute(
                    "SELECT COUNT(commentID)"
                    "FROM Comments WHERE postId=?;", (post_id,))
                comment_count = cur.fetchone()[0]

                cur.execute(
                    "SELECT likes "
                    "FROM POSTS WHERE postId=?;", (post_id,))
                like_count = cur.fetchone()[0]

                liked = check_if_liked(cur, post_id, session["username"])

                all_posts["AllPosts"].append({
                    "postId": user_post[0],
                    "title": user_post[1],
                    "profile_pic": get_profile_picture(user_post[3]),
                    "author": user_post[3],
                    "account_type": account_type,
                    "date_posted": time,
                    "body": (user_post[2])[:250] + add,
                    "post_type": user_post[8],
                    "content": content,
                    "comment_count": comment_count,
                    "like_count": like_count,
                    "liked": liked,
                    "comments": comments
                })
                i += 1
        return all_posts, content, True
    else:
        return all_posts, content, False


def update_comment_achievements(row: int, username: str):
    """
    Unlocks achievements for a user after making a comment.

    Args:
        row: Number of comments on the post.
        username: Author of the post.
    """
    # Award achievement ID 10 - Commentary if necessary
    apply_achievement(session["username"], 10)

    # Award achievement ID 21 - Hot topic if necessary
    if row >= 10:
        apply_achievement(username, 21)


def upload_image(file):
    """
    Uploads the image to the website.

    Args:
        file: The file uploaded by the user.

    Returns:
        The hashed file name.
    """
    file_name_hashed = ""
    # Hashes the name of the file and resizes it.
    if allowed_file(file.filename):
        secure_filename(file.filename)
        file_name_hashed = str(uuid.uuid4())
        file_path = os.path.join(
            "./static/images" + "//post_imgs",
            file_name_hashed)

        img = Image.open(file)
        fixed_height = 600
        height_percent = (fixed_height / float(img.size[1]))
        width_size = int(
            (float(img.size[0]) * float(height_percent)))
        width_size = min(width_size, 800)
        img = img.resize((width_size, fixed_height))
        img = img.convert("RGB")
        img.save(file_path + ".jpg")
    return file_name_hashed


def update_submission_achievements(cur):
    """
    Unlocks achievements for a user after they make a submission.

    Args:
        cur: Cursor for the SQLite database.
    """
    # Award achievement ID 7 - Express yourself if necessary
    apply_achievement(session["username"], 7)

    cur.execute(
        "SELECT * FROM POSTS WHERE username=?;",
        (session["username"],))
    num_posts = cur.fetchall()
    # Award achievement ID 8 - 5 posts if necessary
    if len(num_posts) >= 5:
        apply_achievement(session["username"], 8)
    # Award achievement ID 9 - 20 posts, if necessary
    if len(num_posts) >= 20:
        apply_achievement(session["username"], 9)


def validate_youtube(url: str):
    """
    Checks that the link is a YouTube link.

    Args:
        url: The link input by the user.

    Returns:
        Whether the link is a YouTube link (True/False).
    """
    url_regex = (
        r"(https?://)?(www\.)?"
        "(youtube|youtu|youtube-nocookie)\.(com)/"
        "(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})")
    url_regex_match = re.match(url_regex, url)

    return url_regex_match
