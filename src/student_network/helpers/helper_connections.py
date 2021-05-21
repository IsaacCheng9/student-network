"""
Performs checks and actions to help user connections work effectively.
"""
import os
import sqlite3

from flask import session

import student_network.helpers.helper_general as helper_general
import student_network.helpers.helper_profile as helper_profile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def delete_connection(username: str) -> bool:
    """
    Deletes all connections with the given user.

    Args:
        username: The user to delete all connections with.

    Returns:
        Whether deleting connections was successful (True/False).
    """
    # Checks that the user isn't trying to remove a connection with
    # themselves.
    if username != session["username"]:
        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE username=?;", (username,))

            # Searches for the connection in the database.
            if cur.fetchone() is not None:
                row = cur.execute(
                    "SELECT * FROM Connection WHERE (user1=? AND user2=?) OR "
                    "(user1=? AND user2=?);",
                    (username, session["username"], session["username"], username),
                )
                # Removes the connection from the database if it exists.
                if row:
                    cur.execute(
                        "DELETE FROM Connection WHERE (user1=? AND user2=?) "
                        "OR (user1=? AND user2=?);",
                        (username, session["username"], session["username"], username),
                    )
                    row = cur.execute(
                        "SELECT * FROM Connection "
                        "WHERE (user1=? AND user2=?) "
                        "OR (user1=? AND user2=?);",
                        (username, session["username"], session["username"], username),
                    )
                    if row:
                        cur.execute(
                            "DELETE FROM CloseFriend "
                            "WHERE (user1=? AND user2=?) "
                            "OR (user1=? AND user2=?);",
                            (
                                username,
                                session["username"],
                                session["username"],
                                username,
                            ),
                        )
                    conn.commit()
                    return True
                else:
                    return True
            else:
                return False


def get_connection_request_count() -> int:
    """
    Counts number of pending connection requests for a user.

    Returns:
        The number of pending connection requests for a user.
    """

    if "username" not in session:
        return 0

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM Connection WHERE user2=? AND " "connection_type='request';",
            (session["username"],),
        )
        return len(list(cur.fetchall()))


def get_connection_type(username: str):
    """
    Checks what type of connection the user has with the specified user.

    Args:
        username: The user to check the connection type with.

    Returns:
        The type of connection with the specified user.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT connection_type FROM Connection WHERE user1=? " "AND user2=?",
            (
                session["username"],
                username,
            ),
        )
        conn.commit()

        # Checks if there is a connection between the two users.
        row = cur.fetchone()
        if row:
            return row[0]
        else:
            cur.execute(
                "SELECT connection_type FROM Connection WHERE user1=? AND " "user2=?",
                (
                    username,
                    session["username"],
                ),
            )
            conn.commit()
            row = cur.fetchone()
            if row:
                if row[0] == "connected":
                    return "connected"
                elif row[0] == "block":
                    return "blocked"
                return "incoming"
            else:
                return None


def get_mutual_connections(
    mutual_connections: dict, mutual: str, recommend_type: str, conec: str,
) -> dict:
    """
    Args:
        mutual_connections: List of mutual connections with the user.
        mutual: Mutual users based on other mutual connections and degree.
        recommend_type: Reason why the user is a suggested connection.
        cone: The connection you have in common 

    Returns:
        A list of mutual connections with the user.
    """

    if mutual in mutual_connections.keys():
        mutual_connections[mutual].append(conec)
    else:
        mutual_connections[mutual] = ([conec])

    return mutual_connections


def get_pending_connections(cur, username: str) -> list:
    """
    Gets pending and requested connections for a user.

    Returns:
        List of pending and requested connections for a user.
    """
    cur.execute(
        "SELECT user2 FROM Connection "
        "WHERE user1=? AND connection_type='request' UNION ALL "
        "SELECT user1 FROM Connection "
        "WHERE user2=? AND connection_type='request'",
        (username, username),
    )
    return cur.fetchall()


def get_mutual_hobbies(cur, username: str, pending: list) -> list:

    cur.execute("SELECT hobby FROM UserHobby WHERE username=?;", (username,))
    hobbies = [x[0] for x in cur.fetchall()]
    shared_users = {}
    for hobby in hobbies:
        cur.execute("SELECT username FROM UserHobby WHERE hobby=?;", (hobby,))
        same_users = [x[0] for x in cur.fetchall() if not x[0] == username if x[0] not in pending]
        shared_users[hobby] = same_users

    #print(shared_users)

    return shared_users


def get_mutual_interests(cur, username: str, pending: list) -> list:

    cur.execute("SELECT interest FROM UserInterests WHERE username=?;", (username,))
    hobbies = [x[0] for x in cur.fetchall()]
    shared_users = {}
    for hobby in hobbies:
        cur.execute("SELECT username FROM UserInterests WHERE interest=?;", (hobby,))
        same_users = [x[0] for x in cur.fetchall() if not x[0] == username if x[0] not in pending]
        shared_users[hobby] = same_users

    #print(shared_users)

    return shared_users

def get_mutual_degree(cur, username: str, pending: list, degree: str) -> list:

    shared_users = []
    if degree != 1:
        cur.execute(
            "SELECT username FROM UserProfile WHERE degree=?;", (degree,)
        )
        shared_users = [x[0] for x in cur.fetchall() if x[0] != username and x[0] not in pending]

    return shared_users
        #recommend_type = "Studies " + str(degree[1])
        #for user in shared_degree:
        #    if len(mutual_connections) < 5:
        #        if user[0] != session["username"] and user[0] not in pending:
        #            mutual_connections = get_mutual_connections(
        #                mutual_connections, mutual, recommend_type
        #            )
        #    else:
        #        break

def calculate_similarity(mutual_connections: list, hobbies: dict, interests: dict, shared_degree: list) -> list:

    score_totals = {}
    for user in mutual_connections.keys():
        for conec in mutual_connections[user]:
            close = False
            
            if user not in score_totals.keys():
                score_totals[user] = [0,0,0,0]

            if is_close_friend(session["username"], conec):
                close = True       

            if close:
                score_totals[user][0] += 50
            else:
                score_totals[user][0] += 10

    print(score_totals)

    for hobby in hobbies.keys():
        for user in hobbies[hobby]:
            if user not in score_totals.keys():
                score_totals[user] = [0,0,0,0]

            score_totals[user][1] += 5

    print(score_totals)
    
    for interest in interests.keys():
        for user in interests[interest]:
            if user not in score_totals.keys():
                score_totals[user] = [0,0,0,0]
                
            score_totals[user][2] += 5

    print(score_totals)

    for user in shared_degree:
        if user not in score_totals.keys():
            score_totals[user] = [0,0,0,0]
            
        score_totals[user][3] += 2

    print(score_totals)

    return score_totals

def get_recommended_connections(username: str) -> list:
    """
    Gets recommended connections for a user based on mutual connections and
    degree.

    Returns:
        List of recommended connections for a user and the number of shared
        connections, as well as users with shared degree or interests.
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        pending = [x[0] for x in get_pending_connections(cur, username)]
        recommend_type = "mutual connection"
        connections = [x[0] for x in helper_general.get_all_connections(username)]
        mutual_connections = {}
        for user in connections:
            user_cons = [x[0] for x in helper_general.get_all_connections(user)]
            for mutual in user_cons:
                #print(mutual, user)
                if mutual != session["username"] and mutual not in pending:
                    mutual_connections = get_mutual_connections(
                        mutual_connections, mutual, recommend_type, user
                    )

        print(mutual_connections)
        hobbies = get_mutual_hobbies(cur, session["username"], pending)
        interests = get_mutual_interests(cur, session["username"], pending)
        degree = helper_profile.get_degree(session["username"])
        shared_degree = get_mutual_degree(cur, session["username"], pending, degree[0])

        score_totals = calculate_similarity(mutual_connections, hobbies, interests, shared_degree)

        recommendations = []
        for student in score_totals.keys():
            index = score_totals[student].index(max(score_totals[student]))
            print(student, index)
            if index == 0:
                count = len(mutual_connections[student])
                label = mutual_connections[student][0]
                if score_totals[student][0] > 50:
                    for conec in mutual_connections[student]:
                        if is_close_friend(session["username"], conec):
                            label = conec
                            break
                main = str(count) + " mutual connections including " + label
            elif index == 1:
                for h in hobbies.keys():
                    if student in hobbies[h]:
                        hobby = h
                        break
                main = "you both enjoy hobbies including " + hobby
            elif index == 2:
                for i in interests.keys():
                    if student in interests[i]:
                        interest = i
                        break
                main = "you are both interested in " + interest
            else:
                main = "you both study " + degree[1]


            recommendations.append([student, main, sum(score_totals[student])])

        recommendations = sorted(recommendations, key=lambda x: x[2], reverse=True)[:5]
        print(recommendations)

        """
        if len(mutual_connections) < 5:
            degree = helper_profile.get_degree(session["username"])
            if degree[0] != 1:
                cur.execute(
                    "SELECT username FROM " "UserProfile WHERE degree=?;", (degree[0],)
                )
                shared_degree = cur.fetchall()
                recommend_type = "Studies " + str(degree[1])
                for user in shared_degree:
                    if len(mutual_connections) < 5:
                        if user[0] != session["username"] and user[0] not in pending:
                            mutual_connections = get_mutual_connections(
                                mutual_connections, mutual, recommend_type
                            )
                    else:
                        break
        """
        return recommendations


def is_close_friend(username1: str, username2: str) -> bool:
    """
    Gets whether the selected user1 has user2 as a close friend.

    Returns:
        Whether the user2 is a close friend of user1 (True/False).
    """
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM CloseFriend WHERE (user1=? AND user2=?);",
            (username1, username2),
        )
        if cur.fetchone():
            return True

    return False
