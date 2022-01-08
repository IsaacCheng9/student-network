import student_network.helpers.helper_general as helper_general


def test_is_allowed_photo_file():
    """
    Tests that only certain file types are accepted for uploading photos.
    """
    file_name = "test.jpg"
    assert helper_general.is_allowed_photo_file(file_name) is True
    invalid_file_name = "test.txt"
    assert helper_general.is_allowed_photo_file(invalid_file_name) is False
