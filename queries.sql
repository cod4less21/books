CREATE EXTENSION pgcrypto;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE,
    password VARCHAR NOT NULL
);

CREATE TABLE books (
    isbn VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE reviews (
    isbn VARCHAR REFERENCES books(isbn),
    userid INTEGER REFERENCES users(id),
    username VARCHAR REFERENCES users(username),
    review VARCHAR NOT NULL,
    rating INTEGER NOT NULL DEFAULT 5 CHECK (rating <= 5 AND rating >= 1),
    PRIMARY KEY(isbn, userid)
);

INSERT INTO users(username, email, password) VALUES ('sagar', 'sagar@sagar.com', crypt('password', gen_salt('bf')) );

SELECT id FROM users WHERE username = :username and password = crypt(:pass, password);
SELECT * FROM books WHERE isbn LIKE ('%{:query}%') OR title LIKE ('%{:query}%') OR author LIKE ('%{:query}%')
SELECT count(*) FROM books WHERE upper(isbn) LIKE ('%X%') OR upper(title) LIKE ('%X%') OR upper(author) LIKE ('%X%') UNION
SELECT count(*) FROM books WHERE lower(isbn) LIKE ('%x%') OR lower(title) LIKE ('%x%') OR lower(author) LIKE ('%x%');