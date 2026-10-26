USE library;

INSERT INTO AUTHOR (name, country) VALUES
('Naguib Mahfouz', 'Egypt'),
('Agatha Christie', 'United Kingdom'),
('George Orwell', 'United Kingdom');

INSERT INTO BOOK (title, price, author_id) VALUES
('Palace Walk', 220.00, 1),
('The Thief and the Dogs', 150.00, 1),
('Murder on the Orient Express', 180.00, 2),
('And Then There Were None', 200.00, 2),
('Animal Farm', 120.00, 3),
('Nineteen Eighty-Four', 250.00, 3);
