"""
Performs checks and actions to help the post system work effectively.
"""
import os
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Tuple

import student_network.helpers.helper_achievements as helper_achievements
import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_profile as helper_profile
import student_network.helpers.helper_connections as helper_connections
from PIL import Image
from flask import request, session
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
    cur.execute(
        "SELECT username FROM UserLikes " "WHERE postId=? AND username=?;",
        (post_id, username),
    )
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
    all_posts = {"AllPosts": []}
    if "username" in session:
        session["prev-page"] = request.url
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()

            connections = helper_general.get_all_connections(session["username"])
            connections.append((session["username"],))
            row = []
            for user in connections:
                if (
                    helper_connections.is_close_friend(user[0], session["username"])
                    or user[0] == session["username"]
                ):
                    cur.execute(
                        "SELECT * FROM POSTS "
                        "WHERE username=? AND postId <= ? "
                        "AND privacy!='private' "
                        "AND privacy!='deleted' "
                        "ORDER BY postId DESC LIMIT ?;",
                        (user[0], starting_id, number),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM POSTS "
                        "WHERE username=? AND postId <= ? "
                        "AND privacy!='private' AND privacy!='close' "
                        "AND privacy!='deleted' "
                        "ORDER BY postId DESC LIMIT ?;",
                        (user[0], starting_id, number),
                    )
                row += cur.fetchall()

            # Sort reverse chronologically
            row = sorted(row, key=lambda x: x[0], reverse=True)
            i = 0

            # account type differentiation in posts db
            for user_post in row:
                if i == int(number):
                    break
                add = ""
                if len(user_post[1]) > 250:
                    add = "..."
                time = datetime.strptime(user_post[4], "%Y-%m-%d").strftime("%d-%m-%y")

                # Get account type
                cur.execute(
                    "SELECT type " "FROM ACCOUNTS WHERE username=? ", (user_post[3],)
                )

                accounts = cur.fetchone()
                account_type = accounts[0]

                post_id = user_post[0]

                cur.execute(
                    "SELECT * FROM Comments WHERE postId=? LIMIT 5;", (post_id,)
                )
                comments = cur.fetchall()

                comments = list(
                    map(
                        lambda x: (
                            x[0],
                            x[1],
                            x[2],
                            x[3],
                            x[4],
                            helper_profile.get_profile_picture(x[1]),
                        ),
                        comments,
                    )
                )

                cur.execute(
                    "SELECT COUNT(commentID)" "FROM Comments WHERE postId=?;",
                    (post_id,),
                )
                comment_count = cur.fetchone()[0]

                cur.execute("SELECT likes " "FROM POSTS WHERE postId=?;", (post_id,))
                like_count = cur.fetchone()[0]

                liked = check_if_liked(cur, post_id, session["username"])

                cur.execute("SELECT (contentUrl) FROM PostContent WHERE postId=?", (post_id,))
                images = cur.fetchall()

                all_posts["AllPosts"].append(
                    {
                        "postId": user_post[0],
                        "profile_pic": helper_profile.get_profile_picture(user_post[3]),
                        "author": user_post[3],
                        "account_type": account_type,
                        "date_posted": time,
                        "body": (user_post[1])[:250] + add,
                        "comment_count": comment_count,
                        "like_count": like_count,
                        "liked": liked,
                        "comments": comments,
                        "images": images
                    }
                )
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
    helper_achievements.apply_achievement(session["username"], 10)

    # Award achievement ID 21 - Hot topic if necessary
    if row >= 10:
        helper_achievements.apply_achievement(username, 21)


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
    if helper_general.allowed_file(file.filename):
        secure_filename(file.filename)
        file_name_hashed = str(uuid.uuid4())
        file_path = os.path.join("./static/images" + "//post_imgs", file_name_hashed)

        img = Image.open(file)
        fixed_height = 600
        height_percent = fixed_height / float(img.size[1])
        width_size = int((float(img.size[0]) * float(height_percent)))
        width_size = min(width_size, 800)
        img = img.resize((width_size, fixed_height))
        img = img.convert("RGB")
        img.save(file_path + ".jpg")
    return file_name_hashed

def delete_file(filename):
    if filename == "": return

    file_path = os.path.join("./static/images"+ "//post_imgs", filename)
    os.remove(file_path)


def update_submission_achievements(cur):
    """
    Unlocks achievements for a user after they make a submission.

    Args:
        cur: Cursor for the SQLite database.
    """
    # Award achievement ID 7 - Express yourself if necessary
    helper_achievements.apply_achievement(session["username"], 7)

    cur.execute("SELECT * FROM POSTS WHERE username=?;", (session["username"],))
    num_posts = cur.fetchall()
    # Award achievement ID 8 - 5 posts if necessary
    if len(num_posts) >= 5:
        helper_achievements.apply_achievement(session["username"], 8)
    # Award achievement ID 9 - 20 posts, if necessary
    if len(num_posts) >= 20:
        helper_achievements.apply_achievement(session["username"], 9)


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
        "(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    )
    url_regex_match = re.match(url_regex, url)

    return url_regex_match

def get_account_type(username):
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT type " "FROM ACCOUNTS WHERE username=?;",
                    (username,),
                )

        return cur.fetchone()