# Lab 3 - Part 2: Library (Books and Authors)
Names : Mariam Ayman Ahmed , Jana Mohamed Deyaa

A small Flask + MySQL website to manage the `library` database (tables `AUTHOR` and `BOOK`), with login / registration and image upload (Bonus).

## Project structure

```
lab3-<2304068/2304069>/
├── problem2_DDL.sql            # creates the database `library` and the tables AUTHOR and BOOK
├── problem2_DML.sql            # seed data: 3 authors and 6 books
├── problem2_users.sql          # users table (login / registration)
├── problem2_bonus_images.sql   # optional: adds the image columns by hand (Bonus)
├── README.md
└── website/
    ├── app.py
    ├── requirements.txt
    ├── .env.example
    ├── templates/              # HTML pages
    └── static/                 # CSS files and uploaded images
```

## Requirements

- Python 3.9 or newer
- MySQL Server (and the `mysql` client or MySQL Workbench)

## 1. Create the database

Open a terminal in the project folder (the one that contains `problem2_DDL.sql`) and run the scripts **in this order**:

```bash
mysql -u root -p < problem2_DDL.sql
mysql -u root -p < problem2_DML.sql
mysql -u root -p < problem2_users.sql
```

You can also open each file in MySQL Workbench and press the Execute button, in the same order.

- `problem2_DDL.sql` deletes and re-creates the `library` database, so it can be re-run at any time.
- `problem2_users.sql` creates the `users` table for login. It does not touch the books and authors, and it is safe to run twice.

## 2. Set up the website

Open a terminal in the `website` folder:

```bash
cd website
```

Create and activate a virtual environment.

Windows (PowerShell or CMD):

```powershell
python -m venv .venv
.venv\Scripts\activate
```

If PowerShell blocks the activation, run `Set-ExecutionPolicy -Scope Process Bypass` first and try again.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the packages:

```bash
pip install -r requirements.txt
```

Create your settings file by copying `.env.example` to `.env`:

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

Open `.env` and set:

- `DB_USER` and `DB_PASSWORD` to your local MySQL user and password
- `SECRET_KEY` to any long random text (it protects the login session)

## 3. Run

From inside the `website` folder (with the virtual environment active):

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser. You will see the **Log in** page. Click **Register** to create an account (password: at least 8 characters), and you will be taken to the library page.

## Features

- Register, log in and log out. Passwords are stored as bcrypt hashes, never as plain text.
- Every library page requires a logged-in user.
- Show a table of the books (`book_id`, `title`, `price`, `author_id`) and a table of the authors.
- Add and edit books and authors.
- Delete a book.
- Delete an author; `ON DELETE CASCADE` deletes that author's books too.

### Bonus: images for books and authors

- Each book can have a **cover** and each author a **photo** (PNG, JPG, GIF or WEBP, up to 5 MB). Images are optional.
- Upload an image with the file field in **Add a book** / **Add an author**, or in **Edit**, where you can also replace or remove the current image.
- Images are saved in `website/static/uploads/books` and `website/static/uploads/authors`. The database only stores the file name, in a nullable column `image_filename` on `BOOK` and `AUTHOR`.
- `problem2_DDL.sql` and `problem2_DML.sql` are unchanged. The website adds the `image_filename` columns by itself when it starts. You can also add them by hand by running `problem2_bonus_images.sql` (safe to run more than once).
- Deleting a book or an author also deletes its image files, including the covers of an author's books.
- If you re-run `problem2_DDL.sql` (it drops the database), the saved image names are lost. The website keeps working, and the columns come back the next time the website starts or an image is uploaded.

## Troubleshooting

- **Access denied for user**: check `DB_USER` and `DB_PASSWORD` in `website/.env`.
- **Unknown database 'library'**: run `problem2_DDL.sql` first (step 1).
- **Table 'library.users' doesn't exist**: run `problem2_users.sql` (step 1).
- **Port 5000 already in use**: close the other program using it, or stop the previous `python app.py` with `Ctrl + C`.

Do not upload your real `.env` file or passwords to GitHub.
