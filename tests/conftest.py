import os
import shutil
import tempfile
import io

import pytest
from flaskr import create_app
from flaskr.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')
_post_image_path = os.path.join(os.path.dirname(__file__), '1.gif')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    post_image_path = tempfile.mkdtemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'POST_IMAGE_FOLDER': post_image_path,
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    shutil.copy(_post_image_path, post_image_path)

    yield app

    os.close(db_fd)
    os.unlink(db_path)
    shutil.rmtree(post_image_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)


@pytest.fixture
def jpeg_file():
    return (io.BytesIO(b"abcdef"), 'test.jpg')
