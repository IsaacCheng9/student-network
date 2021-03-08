import application


def test_validate_edit_profile():
    """Tests that profile editing validation is performed correctly."""
    # Tests invalid details.
    bio = ["good bio"]
    gender = ["Male"]
    dob = []
    hobbies = [["good"]]
    interests = [["good"]]
    for num in range(len(bio)):
        valid, message = application.validate_edit_profile(
            bio[num], gender[num], dob[num], "", hobbies[num], interests[num])
        assert valid is False

    # Tests valid details.

    # Tests null details.
