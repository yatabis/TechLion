import json
import os
from bottle import route, run, request
from bottle import HTTPResponse, template

from typing import Dict, Union

from http_elements import post_validation, json_response
from db import sign_up
import twitter_api
import calendar_api


@route("/")
def hello():
    return "Hi, this is TechLion's application!"


@route("/sign-up", method=["GET", "POST"])
def post_sign_up() -> HTTPResponse:
    user, err = post_validation(request, "name", "google", "twitter")
    if err:
        return err.response
    user, err = sign_up(user.get("name"), user.get("google"), user.get("twitter"))
    if err:
        return err.response
    return json_response(200, user)


@route("/dummy")
def dummy():
    return template("dummy.html")


@route("/ping")
def ping():
    return HTTPResponse()


if __name__ == '__main__':
    run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
