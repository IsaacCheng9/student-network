from ..views.helper import *


def test_allowed_file():
    file_name = "test.jpg"
    invalid_file_name = "test.txt"
    assert allowed_file(file_name) is True
    assert allowed_file(invalid_file_name) is False


def test_calculate_age():
    born = datetime.strptime("2001-12-01", "%Y-%m-%d")
    age = calculate_age(born)
    assert 19 == age
