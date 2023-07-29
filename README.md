# Flaskr—Exercises

Solved [exercises](https://flask.palletsprojects.com/tutorial/next/) for the basic blog app built in the Flask [tutorial](https://flask.palletsprojects.com/tutorial/).

- [x] A detail view to show a single post. Click a post’s title to go to its page.
- [x] Like / unlike a post.
- [x] Comments.
- [x] Tags. Clicking a tag shows all the posts with that tag.
- [x] A search box that filters the index page by name.
- [x] Paged display. Only show 5 posts per page.
- [x] Upload an image to go along with a post.
- [x] Format posts using Markdown.
- [ ] An RSS feed of new posts.


## Install

```shell
# clone the repository
$ git clone https://github.com/NSUSpray/flaskr
$ cd flaskr
```

Create a virtualenv and activate it

```shell
$ python3 -m venv .venv
$ . .venv/bin/activate
```

Or on Windows cmd

```cmd
$ py -3 -m venv .venv
$ .venv\Scripts\activate.bat
```

Install Flaskr

```shell
$ pip install -e .
```


## Run

```shell
$ flask --app flaskr init-db
$ flask --app flaskr run --debug
```

Open http://127.0.0.1:5000 in a browser.


## Test

```shell
$ pip install pytest
$ pytest
```

Run with coverage report

```shell
$ coverage run -m pytest
$ coverage report
$ coverage html  # open htmlcov/index.html in a browser
```
