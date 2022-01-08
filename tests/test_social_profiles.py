import student_network.helpers.helper_profile as helper_profile


def test_invalid_edit_profile():
    """
    Tests that invalid profile editing details are rejected.
    """
    bio = [
        "bio",
        "bio",
        "bio",
        "biobiobiobiobiobiobiobiobiobiobiobiobiobiobio"
        "biobiobiobiobiobiobiobiobiobiobiobiobiobiobio"
        "biobiobiobiobiobiobiobiobiobiobiobiobiobiobio"
        "biobiobiobiobiobiobiobiobi",
    ]
    gender = ["Male", "Male", "bad", "Male"]
    dob = ["2001-05-31", "2001-05-31", "2001-05-31", "2001-05-31"]
    hobbies = [["hobby"], ["badhobbybadhobbybadhobbybadhobby"], ["hobby"], ["hobby"]]
    interests = [
        ["badinterestbadinterestbadinterest"],
        ["interest"],
        ["interest"],
        ["interest"],
    ]
    for num in range(len(bio)):
        valid, _ = helper_profile.validate_edit_profile(
            bio[num], gender[num], dob[num], hobbies[num], interests[num]
        )
        assert valid is False


def test_valid_edit_profile():
    """
    Tests that valid profile editing details are accepted.
    """
    valid, _ = helper_profile.validate_edit_profile(
        "good bio", "Male", "2001-01-31", ["hobby"], ["interest"]
    )
    assert valid is True


def test_null_edit_profile():
    """
    Tests that null profile editing details are accepted.
    """
    valid, _ = helper_profile.validate_edit_profile("", "Male", "", [], [])
    assert valid is True
