import application

def test_allowed_file():
    filename = "test.jpg"
    invalidFilename = "test.txt"
    assert application.allowed_file(filename) == True
    assert application.allowed_file(invalidFilename) == False




