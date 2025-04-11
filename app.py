import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from werkzeug.utils import secure_filename
app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row  # indeks yerine column name ile access etmek uchun. Mes.: row[0] yerine row['id']
    return conn


# Database initialization
def init_db():
    conn = get_db()
    # Create posts table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                header_image TEXT
            )
        ''')

    # Create images table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            )
        ''')

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()
    return render_template("home.html", posts=posts)


@app.route("/create", methods=["GET", "POST"])
def create_post():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']

        # Save header image
        header_image_file = request.files.get('header_image')
        header_image_path = None
        if header_image_file and header_image_file.filename != '':
            header_filename = secure_filename(header_image_file.filename)
            header_image_path = os.path.join('static/uploads', header_filename)
            header_image_file.save(header_image_path)

        # Insert post first
        conn = sqlite3.connect('data.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("INSERT INTO posts (title, content, header_image) VALUES (?, ?, ?)",
                    (title, content, header_image_path))
        post_id = cur.lastrowid

        # Save body images
        body_images = request.files.getlist('body_images')
        for img in body_images:
            if img and img.filename != '':
                filename = secure_filename(img.filename)
                img_path = os.path.join('static/uploads', filename)
                img.save(img_path)
                cur.execute("INSERT INTO images (post_id, image_path) VALUES (?, ?)",
                            (post_id, img_path))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))
    return render_template("create.html")

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5005)
