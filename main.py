import os
from bottle import get, post, run, request
from bottle import HTTPResponse


@get("/")
def hello():
    return "Hi, this is TechLion's application!"


if __name__ == '__main__':
    run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
