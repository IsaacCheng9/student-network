import application
from datetime import date, datetime

def test_allowed_file():
    filename = "test.jpg"
    invalidFilename = "test.txt"
    assert application.allowed_file(filename) == True
    assert application.allowed_file(invalidFilename) == False

def test_calcualte_age():
    born = datetime.strptime("2001-12-01", "%Y-%m-%d")
    age = application.calculate_age(born)
    assert 19 == age

