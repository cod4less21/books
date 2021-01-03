class Book():
    def __init__(self, isbn, title, author, year):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year

class Review():
    def __init__(self, isbn, userid, username, review):
        self.isbn = isbn
        self.userid = userid
        self.username = username
        self.review = review