import application


def test_invalid_edit_profile():
    """Tests that invalid profile editing details are rejected."""
    bio = ["good bio"]
    gender = ["bad"]
    dob = ["2001-05-31"]
    hobbies = [["hobby"]]
    interests = [["interest"]]
    for num in range(len(bio)):
        valid, message = application.validate_edit_profile(
            bio[num], gender[num], dob[num], "", hobbies[num], interests[num])
        assert valid is False


def test_valid_edit_profile():
    """Tests that valid profile editing details are accepted."""
    valid, message = application.validate_edit_profile(
        "good bio", "Male", "2001-01-31", "", ["hobby"], ["interest"])
    assert valid is True


def test_null_edit_profile():
    """Tests that null profile editing details are rejected."""
    valid, message = application.validate_edit_profile(
        "", "", "", "", [], [])
    assert valid is False
