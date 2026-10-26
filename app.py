from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import bcrypt
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.exceptions import RequestEntityTooLarge

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)

print("ENV PATH:", env_path)
print("ENV EXISTS:", env_path.is_file())
print("DB USER:", os.getenv("DB_USER"))
print("PASSWORD LOADED:", bool(os.getenv("DB_PASSWORD")))

app = Flask(__name__)
# The secret key signs the session cookie. It is read from SECRET_KEY in .env.
# If it is missing, a random key is used (everyone is logged out on restart).
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(24).hex()

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "library")
    )


# =====================================================================
# BONUS: images for books (cover) and authors (photo)
# Files are saved in static/uploads/books and static/uploads/authors.
# Only the file name is stored in the database (column image_filename).
# =====================================================================

UPLOAD_ROOT = Path(__file__).resolve().parent / "static" / "uploads"
UPLOAD_FOLDERS = {"books": UPLOAD_ROOT / "books", "authors": UPLOAD_ROOT / "authors"}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB per request

for _folder in UPLOAD_FOLDERS.values():
    _folder.mkdir(parents=True, exist_ok=True)


def ensure_image_columns():
    """Add the image_filename column to BOOK and AUTHOR if it is missing.

    This keeps problem2_DDL.sql unchanged: after you run the DDL + DML, the
    website adds the new column by itself (same as problem2_bonus_images.sql).
    """
    db = get_db()
    cur = db.cursor()
    try:
        for table in ("BOOK", "AUTHOR"):
            cur.execute(f"SHOW COLUMNS FROM {table} LIKE 'image_filename'")
            if not cur.fetchall():
                cur.execute(f"ALTER TABLE {table} ADD COLUMN image_filename VARCHAR(255) NULL")
        db.commit()
    finally:
        cur.close()
        db.close()


try:
    ensure_image_columns()
except Exception as error:  # the database may not be ready yet; the app still starts
    print("Could not check the image columns:", error)


def looks_like_image(header):
    """Check the first bytes of the file, not only its extension."""
    return (
        header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"GIF87a")
        or header.startswith(b"GIF89a")
        or (header[:4] == b"RIFF" and header[8:12] == b"WEBP")
    )


def save_image(upload, kind):
    """Save an uploaded image. Returns (file_name, error_message)."""
    extension = os.path.splitext(upload.filename)[1].lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        return None, "Image must be a PNG, JPG, GIF or WEBP file."
    if not looks_like_image(upload.stream.read(16)):
        return None, "That file is not a valid image."
    upload.stream.seek(0)
    file_name = uuid.uuid4().hex + "." + extension
    try:
        ensure_image_columns()  # in case the DDL was re-run while the site was open
    except Exception:
        pass
    upload.save(UPLOAD_FOLDERS[kind] / file_name)
    return file_name, None


def delete_image_file(file_name, kind):
    """Remove an image file from disk (does nothing if it does not exist)."""
    if file_name:
        try:
            (UPLOAD_FOLDERS[kind] / file_name).unlink()
        except OSError:
            pass


def image_names(cur, query, params):
    """Read image file names; returns [] if the image column does not exist."""
    try:
        cur.execute(query, params)
        return [row["image_filename"] for row in cur.fetchall() if row["image_filename"]]
    except mysql.connector.Error:
        return []


@app.errorhandler(RequestEntityTooLarge)
def image_too_large(error):
    flash("The image is too large. The maximum size is 5 MB.")
    return redirect(request.referrer or url_for("home"))


# =====================================================================
# Login / Registration / Logout
# (same logic as the To-Do assignment, adapted for the Library)
# =====================================================================

# Pages that can be opened WITHOUT logging in. Everything else is protected.
PUBLIC_PAGES = {"login", "register", "static"}


@app.before_request
def require_login():
    """Runs before every request: logged-out users are sent to the login page.

    This is the same check as `if "user_id" not in session` from the To-Do
    assignment, written once here instead of inside every route.
    """
    if request.endpoint in PUBLIC_PAGES:
        return None
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    errors = {}
    form = {"name": "", "email": ""}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        form = {"name": name, "email": email}

        if not name:
            errors["name"] = "Name is required"
        elif len(name) > 100:
            errors["name"] = "Name is too long"

        if not email:
            errors["email"] = "Email is required"
        elif "@" not in email or len(email) > 255:
            errors["email"] = "Enter a valid email address"

        if not password:
            errors["password"] = "Password is required"
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters"

        if not confirm_password:
            errors["confirm_password"] = "Confirm password is required"
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match"

        if errors:
            return render_template("register.html", errors=errors, form=form)

        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                errors["email"] = "Email already exists"
                return render_template("register.html", errors=errors, form=form)

            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                (email, name, password_hash),
            )
            db.commit()

            session.clear()
            session["user_id"] = cur.lastrowid
            session["name"] = name
        finally:
            cur.close()
            db.close()

        flash(f"Welcome to the library, {name}!")
        return redirect(url_for("home"))

    return render_template("register.html", errors=errors, form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    errors = {}
    email = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email:
            errors["email"] = "Email is required"
        if not password:
            errors["password"] = "Password is required"

        if errors:
            return render_template("login.html", errors=errors, email=email)

        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
        finally:
            cur.close()
            db.close()

        if user and bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        ):
            session.clear()
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            flash(f"Welcome back, {user['name']}!")
            return redirect(url_for("home"))

        # Same message for wrong email and wrong password, so nobody can
        # find out which emails are registered.
        errors["general"] = "Invalid email or password"

    return render_template("login.html", errors=errors, email=email)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# =====================================================================
# Library pages (unchanged)
# =====================================================================

@app.route("/")
def home():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM BOOK ORDER BY book_id DESC")
    books = cur.fetchall()
    cur.execute("SELECT * FROM AUTHOR ORDER BY author_id DESC")
    authors = cur.fetchall()
    cur.close()
    db.close()
    return render_template("index.html", books=books, authors=authors)

@app.route("/authors/add", methods=["POST"])
def add_author():
    name = request.form.get("name", "").strip()
    country = request.form.get("country", "").strip()
    if not name or not country:
        flash("Please enter the author name and country.")
        return redirect(url_for("home"))
    photo = None
    upload = request.files.get("image")
    if upload and upload.filename:
        photo, error = save_image(upload, "authors")
        if error:
            flash(error)
            return redirect(url_for("home"))
    db = get_db()
    cur = db.cursor()
    if photo:
        cur.execute("INSERT INTO AUTHOR (name, country, image_filename) VALUES (%s, %s, %s)",
                    (name, country, photo))
    else:
        cur.execute("INSERT INTO AUTHOR (name, country) VALUES (%s, %s)", (name, country))
    db.commit()
    cur.close()
    db.close()
    flash("Author added.")
    return redirect(url_for("home"))

@app.route("/authors/edit/<int:author_id>", methods=["GET", "POST"])
def edit_author(author_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        country = request.form.get("country", "").strip()
        if not name or not country:
            flash("Name and country are required.")
            cur.execute("SELECT * FROM AUTHOR WHERE author_id = %s", (author_id,))
            author = cur.fetchone()
            cur.close()
            db.close()
            return render_template("edit_author.html", author=author)
        photo = None
        upload = request.files.get("image")
        if upload and upload.filename:
            photo, error = save_image(upload, "authors")
            if error:
                flash(error)
                cur.execute("SELECT * FROM AUTHOR WHERE author_id = %s", (author_id,))
                author = cur.fetchone()
                cur.close()
                db.close()
                return render_template("edit_author.html", author=author)
        old_photos = []
        if photo or request.form.get("remove_image"):
            old_photos = image_names(cur, "SELECT image_filename FROM AUTHOR WHERE author_id = %s",
                                     (author_id,))
        cur.execute("UPDATE AUTHOR SET name=%s, country=%s WHERE author_id=%s",
                    (name, country, author_id))
        if photo:
            cur.execute("UPDATE AUTHOR SET image_filename=%s WHERE author_id=%s", (photo, author_id))
        elif request.form.get("remove_image") and old_photos:
            cur.execute("UPDATE AUTHOR SET image_filename=NULL WHERE author_id=%s", (author_id,))
        db.commit()
        if photo or request.form.get("remove_image"):
            for old in old_photos:
                if old != photo:
                    delete_image_file(old, "authors")
        cur.close()
        db.close()
        return redirect(url_for("home"))
    cur.execute("SELECT * FROM AUTHOR WHERE author_id = %s", (author_id,))
    author = cur.fetchone()
    cur.close()
    db.close()
    if not author:
        return "Author not found", 404
    return render_template("edit_author.html", author=author)

@app.route("/authors/delete/<int:author_id>", methods=["POST"])
def delete_author(author_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    # Remember the image files first: the author's books are deleted by ON DELETE CASCADE.
    author_photos = image_names(cur, "SELECT image_filename FROM AUTHOR WHERE author_id = %s",
                                (author_id,))
    book_covers = image_names(cur, "SELECT image_filename FROM BOOK WHERE author_id = %s",
                              (author_id,))
    cur.execute("DELETE FROM AUTHOR WHERE author_id = %s", (author_id,))
    db.commit()
    for name in author_photos:
        delete_image_file(name, "authors")
    for name in book_covers:
        delete_image_file(name, "books")
    cur.close()
    db.close()
    flash("Author deleted. Their books are deleted automatically.")
    return redirect(url_for("home"))

@app.route("/books/add", methods=["POST"])
def add_book():
    title = request.form.get("title", "").strip()
    price = request.form.get("price", "").strip()
    author_id = request.form.get("author_id", "").strip()
    if not title or not price or not author_id:
        flash("Please fill in all book fields.")
        return redirect(url_for("home"))
    try:
        price = float(price)
        if price < 0:
            raise ValueError
        author_id = int(author_id)
    except ValueError:
        flash("Enter a valid non-negative price and author.")
        return redirect(url_for("home"))
    cover = None
    upload = request.files.get("image")
    if upload and upload.filename:
        cover, error = save_image(upload, "books")
        if error:
            flash(error)
            return redirect(url_for("home"))
    db = get_db()
    cur = db.cursor()
    if cover:
        cur.execute("INSERT INTO BOOK (title, price, author_id, image_filename) VALUES (%s, %s, %s, %s)",
                    (title, price, author_id, cover))
    else:
        cur.execute("INSERT INTO BOOK (title, price, author_id) VALUES (%s, %s, %s)",
                    (title, price, author_id))
    db.commit()
    cur.close()
    db.close()
    flash("Book added.")
    return redirect(url_for("home"))

@app.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price = request.form.get("price", "").strip()
        author_id = request.form.get("author_id", "").strip()
        try:
            price = float(price)
            author_id = int(author_id)
            if not title or price < 0:
                raise ValueError
        except ValueError:
            cur.execute("SELECT * FROM BOOK WHERE book_id=%s", (book_id,))
            book = cur.fetchone()
            cur.execute("SELECT * FROM AUTHOR ORDER BY name")
            authors = cur.fetchall()
            cur.close()
            db.close()
            flash("Enter a title, valid price, and author.")
            return render_template("edit_book.html", book=book, authors=authors)
        cover = None
        upload = request.files.get("image")
        if upload and upload.filename:
            cover, error = save_image(upload, "books")
            if error:
                flash(error)
                cur.execute("SELECT * FROM BOOK WHERE book_id=%s", (book_id,))
                book = cur.fetchone()
                cur.execute("SELECT * FROM AUTHOR ORDER BY name")
                authors = cur.fetchall()
                cur.close()
                db.close()
                return render_template("edit_book.html", book=book, authors=authors)
        old_covers = []
        if cover or request.form.get("remove_image"):
            old_covers = image_names(cur, "SELECT image_filename FROM BOOK WHERE book_id=%s",
                                     (book_id,))
        cur.execute("UPDATE BOOK SET title=%s, price=%s, author_id=%s WHERE book_id=%s",
                    (title, price, author_id, book_id))
        if cover:
            cur.execute("UPDATE BOOK SET image_filename=%s WHERE book_id=%s", (cover, book_id))
        elif request.form.get("remove_image") and old_covers:
            cur.execute("UPDATE BOOK SET image_filename=NULL WHERE book_id=%s", (book_id,))
        db.commit()
        if cover or request.form.get("remove_image"):
            for old in old_covers:
                if old != cover:
                    delete_image_file(old, "books")
        cur.close()
        db.close()
        return redirect(url_for("home"))
    cur.execute("SELECT * FROM BOOK WHERE book_id=%s", (book_id,))
    book = cur.fetchone()
    cur.execute("SELECT * FROM AUTHOR ORDER BY name")
    authors = cur.fetchall()
    cur.close()
    db.close()
    if not book:
        return "Book not found", 404
    return render_template("edit_book.html", book=book, authors=authors)

@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    covers = image_names(cur, "SELECT image_filename FROM BOOK WHERE book_id=%s", (book_id,))
    cur.execute("DELETE FROM BOOK WHERE book_id=%s", (book_id,))
    db.commit() 
    for name in covers:
        delete_image_file(name, "books")
    cur.close()
    db.close()
    flash("Book deleted.")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
