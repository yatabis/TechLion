import os
from bottle import get, post, run, request
from bottle import HTTPResponse, template

import twitter_api
import calendar_api


@get("/")
def hello():
    return "Hi, this is TechLion's application!"


@get("/dummy")
def dummy():
    return template("dummy.html")


if __name__ == '__main__':
    run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
