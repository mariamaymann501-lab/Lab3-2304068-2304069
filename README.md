# Lab 3 - Part 2: Library

## 1. Create the database
Open MySQL Workbench and run `problem2_DDL.sql`, then run `problem2_DML.sql`.

Then run `problem2_users.sql` to create the `users` table for Login / Registration.
If your database already has books and authors, run **only** `problem2_users.sql`;
it keeps your existing data (`problem2_DDL.sql` deletes the whole database).

## 2. Set up the website
Open a terminal in the `website` folder and run:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Install the packages:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then update `DB_USER` and `DB_PASSWORD` to match your local MySQL setup, and set `SECRET_KEY` to any long random text (it protects the login session).

## 3. Run
From inside `website`:

```bash
python app.py
```

Open `http://127.0.0.1:5000`. You will see the **Log in** page; click **Register** to create an account first.

## Features
- Register, log in and log out. Passwords are stored as bcrypt hashes, never as plain text.
- Every library page and action requires a logged-in user (checked in `@app.before_request`).
- Show books with `book_id`, `title`, `price`, and `author_id`.
- Show authors.
- Add and edit books and authors.
- Delete a book.
- Delete an author; `ON DELETE CASCADE` deletes that author's books too.

## Bonus: images for books and authors
- Each book can have a **cover** and each author a **photo** (PNG, JPG, GIF or WEBP, up to 5 MB). Images are optional.
- Upload one with the file field in **Add a book** / **Add an author**, or in **Edit**, where you can also replace or remove the current image.
- Images are saved in `website/static/uploads/books` and `website/static/uploads/authors`. The database only stores the file name, in a new nullable column `image_filename` on `BOOK` and `AUTHOR`.
- `problem2_DDL.sql` and `problem2_DML.sql` are **unchanged**. The website adds the `image_filename` columns by itself when it starts. You can also add them by hand by running `problem2_bonus_images.sql` (safe to run more than once).
- Deleting a book or an author also deletes its image files, including the covers of an author's books.
- If you re-run `problem2_DDL.sql` (it drops the database), the old image names are lost. The website keeps working; the columns come back the next time the website starts or an image is uploaded.

Do not upload your real `.env` file or passwords to GitHub.
