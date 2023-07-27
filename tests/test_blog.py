import pytest
from flaskr.db import get_db


def test_index(client, auth):
    response = client.get('/')
    assert b'Log In' in response.data
    assert b'Register' in response.data
    assert '🤍&nbsp;1' in response.data.decode('utf-8')
    assert '💬&nbsp;1' in response.data.decode('utf-8')
    assert b'Search' in response.data
    assert b'Pages:' in response.data

    auth.login()
    response = client.get('/')
    assert b'Log Out' in response.data
    assert b'test title' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/1/update"' in response.data
    assert '💙&nbsp;1' in response.data.decode('utf-8')


def test_show_tagged(client):
    response = client.get('/tag/test_tag')
    assert 'with tag “test_tag”' in response.data.decode('utf-8')
    assert b'test title 1' in response.data
    assert b'test title 2' not in response.data


def test_search(client):
    response = client.get('/?search=title')
    assert 'for “title”' in response.data.decode('utf-8')
    assert b'test title 1' in response.data
    assert b'test title 2' in response.data
    response = client.get('/?search=title 1')
    assert b'test title 1' in response.data
    assert b'test title 2' not in response.data


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
    '/1/like',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.execute('UPDATE comment SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/update"' not in client.get('/').data
    # current user can't delete other user's comment
    assert client.post('/delete_comment/1').status_code == 403


@pytest.mark.parametrize('path', (
    '/8/update',
    '/8/delete',
    '/8/like',
    '/delete_comment/2',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app, jpeg_file):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post(
        '/create',
        data={'title': 'created', 'body': '', 'tags': '', 'image': jpeg_file},
        content_type='multipart/form-data',
    )

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 8


def test_read(client, auth):
    response = client.get('/1')
    assert b'test title' in response.data
    assert b'by test on 2018-01-01' in response.data
    assert b'test\nbody' in response.data
    assert '🤍&nbsp;1' in response.data.decode('utf-8')
    assert b'1 comments' in response.data
    assert b'test_tag' in response.data

    auth.login()
    response = client.get('/1')
    assert b'href="/1/update"' in response.data
    assert b'action="/1/like"' in response.data
    assert '💙&nbsp;1' in response.data.decode('utf-8')


def test_update(client, auth, app, jpeg_file):
    auth.login()
    assert client.get('/1/update').status_code == 200
    response = client.post(
        '/1/update',
        data={'title': 'updated', 'body': '', 'tags': '', 'image': jpeg_file},
        content_type='multipart/form-data',
    )
    assert response.headers['Location'] == '/1'

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
))
def test_create_update_validate(client, auth, jpeg_file, path):
    auth.login()
    response = client.post(
        path,
        data={'title': '', 'body': '', 'tags': '', 'image': jpeg_file},
        content_type='multipart/form-data',
    )
    assert b'Title is required.' in response.data


def test_comment_validate(client, auth):
    auth.login()
    response = client.post('/1/comment', data={'body': ''})
    assert b'Message is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers['Location'] == '/'

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None


def test_like(client, auth, app):
    def get_count():
        with app.app_context():
            db = get_db()
            count = db.execute('''
                SELECT COUNT(*) FROM reaction
                WHERE post_id = 1 AND user_id = 1'''
            ).fetchone()[0]
        return count

    auth.login()

    for i in range(2):
        response = client.post('/1/like')
        assert response.headers['Location'] == '/1'
        assert get_count() == i


def test_comment(client, auth, app):
    auth.login()
    client.post('/1/comment', data={'body': 'hello'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM comment').fetchone()[0]
        assert count == 2


def test_delete_comment(client, auth, app):
    auth.login()
    response = client.post('/delete_comment/1')
    assert response.headers['Location'] == '/1'

    with app.app_context():
        db = get_db()
        comment = db.execute('SELECT * FROM comment WHERE id = 1').fetchone()
        assert comment is None


def test_pages(client):
    response = client.get('/')
    assert b'title="Previous page"' not in response.data
    assert b'<span>1</span>' in response.data
    assert b'href="/?start=5"' in response.data

    response = client.get('/?start=5')
    assert b'href="/?start=0"' in response.data
    assert b'<span>2</span>' in response.data
    assert b'title="Next page"' not in response.data

    response = client.get('/?start=1')
    assert b'href="/?start=0"' in response.data
    assert b'<span>2</span>' in response.data
    assert b'href="/?start=6"' in response.data
