import json
import os
from bottle import get, post, run, request
from bottle import HTTPResponse, template

import twitter_api
import calendar_api
from db import sign_up, fetch_user

JSON_HEADER = {"Content-Type": "application/json"}


def json_response(status_code: int, body: dict) -> HTTPResponse:
    return HTTPResponse(status=status_code, body=json.dumps(body, ensure_ascii=False), headers=JSON_HEADER)


@get("/")
def hello():
    return "Hi, this is TechLion's application!"


@post("/sign-up")
def post_sign_up():
    user = request.json
    if user is None:
        return json_response(400, {"error": {"message": {"The field `user_id` is empty."}}})
    resp = sign_up(user.get("google"), user.get("twitter"))
    if not isinstance(resp, str):
        return json_response(400, resp)
    header = JSON_HEADER
    header["Location"] = f"https://hacku-techlion.herokuapp.com/users/{resp}"
    return HTTPResponse(status=200, body=json.dumps({"user": get_user(resp).body}, ensure_ascii=False), headers=header)


@get("/users/<user_id>")
def get_user(user_id: str) -> HTTPResponse:
    user = fetch_user(user_id)
    if user is None:
        return json_response(404, body={"error": f"User {user_id} does not exist."})
    return json_response(200, body=user)


@get("/dummy")
def dummy():
    return template("dummy.html")


if __name__ == '__main__':
    run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
