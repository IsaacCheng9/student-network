from flask import Flask, session, url_for, request

import application


def test_invalid_edit_profile():
    """Tests that invalid profile editing details are rejected."""
    bio = ["bio", "bio", "bio", "biobiobiobiobiobiobiobiobiobiobiobiobiobiobio"
                                "biobiobiobiobiobiobiobiobiobiobiobiobiobiobio"
                                "biobiobiobiobiobiobiobiobiobiobiobiobiobiobio"
                                "biobiobiobiobiobiobiobiobi"]
    gender = ["Male", "Male", "bad", "Male"]
    dob = ["2001-05-31", "2001-05-31", "2001-05-31", "2001-05-31"]
    hobbies = [["hobby"], ["badhobbybadhobbybadhobbybadhobby"], ["hobby"],
               ["hobby"]]
    interests = [["badinterestbadinterestbadinterest"], ["interest"],
                 ["interest"], ["interest"]]
    for num in range(len(bio)):
        valid, message = application.validate_edit_profile(
            bio[num], gender[num], dob[num], hobbies[num], interests[num])
        assert valid is False


def test_valid_edit_profile():
    """Tests that valid profile editing details are accepted."""
    valid, message = application.validate_edit_profile(
        "good bio", "Male", "2001-01-31", ["hobby"], ["interest"])
    assert valid is True


def test_null_edit_profile():
    """Tests that null profile editing details are accepted."""
    valid, message = application.validate_edit_profile(
        "", "Male", "", [], [])
    assert valid is True

def test_invalid_user_profile_route():
    app = application.application
    client = app.test_client()
    url = '/profile'

    with client:
        response = client.get(url, follow_redirects=True)
        assert request.path == url_for('index_page')

def test_valid_profile_route():
    app = application.application
    client = app.test_client()
    with client.session_transaction() as session:
        session["username"] = 'barn354'
    url = '/profile/barn354'

    with client:
        response = client.get(url)
        assert response.status_code == 200
        assert request.path == url_for('profile', username='barn354')
