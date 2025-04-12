import os
import csv
import json
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row  # Access columns by name
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

    # For each post, fetch associated images
    body_images = []
    for post in posts:
        images = conn.execute("SELECT * FROM images WHERE post_id = ?", (post['id'],)).fetchall()
        body_images.extend(images)

    conn.close()
    return render_template("home.html", posts=posts, body_images=body_images)


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
            header_image_path = f"static/uploads/{header_filename}"
            header_image_file.save(os.path.join('static', 'uploads', header_filename))

        # Insert post
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO posts (title, content, header_image) VALUES (?, ?, ?)",
                    (title, content, header_image_path))
        post_id = cur.lastrowid

        # Save body images
        body_images = request.files.getlist('body_images')
        for img in body_images:
            if img and img.filename != '':
                filename = secure_filename(img.filename)
                save_path = os.path.join('static', 'uploads', filename)
                img.save(save_path)
                web_path = f'static/uploads/{filename}'
                cur.execute("INSERT INTO images (post_id, image_path) VALUES (?, ?)", (post_id, web_path))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))
    return render_template("create.html")


@app.route("/statistics")
def statistics():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()

    total_posts = len(posts)
    total_words = 0
    total_characters = 0
    post_stats = []

    for post in posts:
        words = post["content"].split()
        word_count = len(words)
        char_count = len(post["content"])
        total_words += word_count
        total_characters += char_count

        post_stats.append({
            "title": post["title"],
            "word_count": word_count,
            "char_count": char_count
        })

    labels = [stat["title"] for stat in post_stats]
    word_counts = [stat["word_count"] for stat in post_stats]
    char_counts = [stat["char_count"] for stat in post_stats]

    return render_template("statistics.html",
                           total_posts=total_posts,
                           total_words=total_words,
                           total_characters=total_characters,
                           post_stats=post_stats,
                           labels=labels,
                           word_counts=word_counts,
                           char_counts=char_counts)


@app.route("/developers")
def developers():
    return render_template("developers.html")


@app.route("/export/json")
def export_json():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()

    post_list = [dict(post) for post in posts]
    json_data = json.dumps(post_list, indent=4)

    return Response(
        json_data,
        mimetype='application/json',
        headers={"Content-Disposition": "attachment;filename=posts.json"}
    )


@app.route("/export/csv")
def export_csv():
    conn = get_db()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'title', 'content', 'header_image'])

    for post in posts:
        writer.writerow([
            post['id'],
            post['title'],
            post['content'],
            post['header_image']
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=posts.csv"}
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5005)
