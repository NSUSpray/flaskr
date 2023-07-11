from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute('''
        SELECT p.id, title, body, created, author_id, username
        FROM post p JOIN user u ON p.author_id = u.id
        ORDER BY created DESC
    ''').fetchall()
    reactions = [get_reactions(post['id']) for post in posts]
    return render_template(
        'blog/index.html.jinja', posts=posts, reactions=reactions
    )


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('''
                INSERT INTO post (title, body, author_id)
                VALUES (?, ?, ?)''',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html.jinja')


def get_post(id, check_author=True):
    post = get_db().execute('''
        SELECT p.id, title, body, created, author_id, username
        FROM post p JOIN user u ON p.author_id = u.id
        WHERE p.id = ?''',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


def get_reactions(post_id):
    db = get_db()
    reactions = db.execute('''
        SELECT user_id
        FROM reaction r
        WHERE post_id = ?''',
        (post_id,)
    ).fetchall()
    return [reaction['user_id'] for reaction in reactions]


@bp.route('/<int:id>')
def read(id):
    post = get_post(id, check_author=False)
    reactions = get_reactions(post['id'])
    return render_template(
        'blog/read.html.jinja', post=post, reactions=reactions
    )


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('''
                UPDATE post SET title = ?, body = ?
                WHERE id = ?''',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html.jinja', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/like', methods=('POST',))
@login_required
def like(id):
    post = get_post(id, check_author=False)
    liked = g.user['id'] in get_reactions(post['id'])
    db = get_db()
    if liked:
        db.execute('''
            DELETE FROM reaction
            WHERE post_id = ? AND user_id = ?''',
            (post['id'], g.user['id'])
        )
    else:
        db.execute('''
            INSERT INTO reaction (post_id, user_id)
            VALUES (?, ?)''',
            (post['id'], g.user['id'])
        )
    db.commit()
    return redirect(url_for('blog.read', id=id))
