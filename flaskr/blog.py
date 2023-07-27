from math import floor
from pathlib import Path
import glob

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
    current_app, send_from_directory
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db


POSTS_PER_PAGE = 5
ALLOWED_EXTENSIONS = {'.jpe', '.jpg', '.jpeg', '.gif', '.png', '.bmp', '.webp'}

bp = Blueprint('blog', __name__)


@bp.route('/')
@bp.route('/tag/<tag>')
def index(tag=None):
    search = request.args.get('search')
    try:
        start = int(request.args.get('start'))
    except (ValueError, TypeError):
        start = 0
    else:
        start = max(start, 0)

    db = get_db()
    where_order_request = '''
        WHERE " " || tags || " " LIKE ?
        AND title LIKE ?
        ORDER BY created DESC
    '''
    where_values = (
        f'% {tag} %' if tag else '%',
        f'%{search}%' if search else '%',
    )
    posts = db.execute('''
        SELECT p.id, title, body, created, author_id, username
        FROM post p JOIN user u ON p.author_id = u.id'''
        + where_order_request + 'LIMIT ? OFFSET ?',
        where_values + (POSTS_PER_PAGE, start),
    ).fetchall()
    last = db.execute(
        'SELECT COUNT(*) AS c FROM post' + where_order_request,
        where_values,
    ).fetchone()['c'] - 1

    reactions = [get_reactions(post['id']) for post in posts]
    comments = [get_comments(post['id']) for post in posts]
    prv = max(start - POSTS_PER_PAGE, 0) if start > 0 else None
    nxt = start + POSTS_PER_PAGE if start + POSTS_PER_PAGE <= last else None
    current_page = floor((start - 1) / POSTS_PER_PAGE) + 2

    return render_template(
        'blog/index.html.jinja',
        posts=posts,
        reactions=reactions,
        comments=comments,
        tag=tag,
        search=search,
        prev=prv,
        current_page=current_page,
        next=nxt,
    )


def make_tag_list(tags_string):
    return [tag for tag in tags_string.split(' ') if tag]


def allowed_file(filename):
    return '.' in filename and \
           Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def image_path(id, orig_filename=None):
    root_dir = Path(
        current_app.instance_path,
        current_app.config['POST_IMAGE_FOLDER']
    )
    if orig_filename:
        return Path(root_dir, str(id)).with_suffix(Path(orig_filename).suffix)
    else:
        paths = glob.glob(f'{id}*', root_dir=root_dir)
        if paths:
            return Path(current_app.config['POST_IMAGE_FOLDER'], paths[0])


def remove_images(id):
    root_dir = Path(
        current_app.instance_path,
        current_app.config['POST_IMAGE_FOLDER']
    )
    for path in glob.glob(f'{id}*', root_dir=root_dir):
        Path(root_dir, path).unlink()


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = make_tag_list(request.form['tags'])
        error = None

        if not title:
            error = 'Title is required.'
        elif 'image' not in request.files:
            error = 'No file part.'
        else:
            file = request.files['image']
            if file.filename and file and not allowed_file(file.filename):
                error = 'Invalid image file type.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('''
                INSERT INTO post (title, body, author_id, tags)
                VALUES (?, ?, ?, ?)''',
                (title, body, g.user['id'], ' '.join(tags))
            )
            db.commit()
            id = db.execute('SELECT LAST_INSERT_ROWID() id').fetchone()['id']
            if file.filename:
                path = image_path(id, file.filename)
                file.save(path)
            return redirect(url_for('blog.read', id=str(id)))

    return render_template('blog/create.html.jinja')


def get_post(id, check_author=True):
    post = get_db().execute('''
        SELECT p.id, title, body, created, author_id, username, tags
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
    reactions = get_db().execute(
        'SELECT user_id FROM reaction WHERE post_id = ?',
        (post_id,)
    ).fetchall()
    return [reaction['user_id'] for reaction in reactions]


def get_comments(post_id):
    comments = get_db().execute('''
        SELECT c.id, body, created, author_id, username
        FROM comment c JOIN user u ON c.author_id = u.id
        WHERE post_id = ?
        ORDER BY created DESC''',
        (post_id,)
    ).fetchall()
    return comments


def get_comment(id, check_author=True):
    comment = get_db().execute('''
        SELECT c.id, body, created, author_id, post_id, username
        FROM comment c JOIN user u ON c.author_id = u.id
        WHERE c.id = ?''',
        (id,)
    ).fetchone()

    if comment is None:
        abort(404, f"Comment id {id} doesn't exist.")

    if check_author and comment['author_id'] != g.user['id']:
        abort(403)

    return comment


@bp.route('/<int:id>')
def read(id):
    post = get_post(id, check_author=False)
    reactions = get_reactions(id)
    comments = get_comments(id)
    tags = make_tag_list(post['tags'])
    path = image_path(id)
    ext = path and path.suffix
    return render_template(
        'blog/read.html.jinja',
        post=post, reactions=reactions, comments=comments, tags=tags,
        image_ext=ext,
    )


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = make_tag_list(request.form['tags'])
        error = None

        if not title:
            error = 'Title is required.'
        elif 'image' not in request.files:
            error = 'No file part.'
        else:
            file = request.files['image']
            if file.filename and file and not allowed_file(file.filename):
                error = 'Invalid image file type.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute('''
                UPDATE post SET title = ?, body = ?, tags = ?
                WHERE id = ?''',
                (title, body, ' '.join(tags), id)
            )
            db.commit()
            remove_images(id)
            if file.filename:
                path = image_path(id, file.filename)
                file.save(path)
            return redirect(url_for('blog.read', id=id))

    return render_template('blog/update.html.jinja', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    remove_images(id)
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


@bp.route('/<int:id>/comment', methods=('POST',))
def comment(id):
    body = request.form['body']
    error = None

    if not body:
        error = 'Message is required.'

    if error is not None:
        flash(error)
        return read(id)
    else:
        db = get_db()
        db.execute('''
            INSERT INTO comment (body, author_id, post_id)
            VALUES (?, ?, ?)''',
            (body, g.user['id'], id)
        )
        db.commit()
        return redirect(url_for('blog.read', id=id))


@bp.route('/delete_comment/<int:id>', methods=('POST',))
@login_required
def delete_comment(id):
    comment = get_comment(id)
    db = get_db()
    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.read', id=comment['post_id']))


@bp.route('/<id>/image<ext>')
def get_image(id, ext):
    root_dir = Path(
        current_app.instance_path,
        current_app.config['POST_IMAGE_FOLDER']
    )
    return send_from_directory(root_dir, f'{id}{ext}')
