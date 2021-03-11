from datetime import datetime

import application


def test_allowed_file():
    file_name = "test.jpg"
    invalid_file_name = "test.txt"
    assert application.allowed_file(file_name) is True
    assert application.allowed_file(invalid_file_name) is False


def test_calculate_age():
    born = datetime.strptime("2001-12-01", "%Y-%m-%d")
    age = application.calculate_age(born)
    assert 19 == age
