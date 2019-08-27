from datetime import datetime
import json
import os
from bottle import get, request, redirect
from bottle import HTTPResponse
from pytz import timezone
from requests import Response
from requests_oauthlib import OAuth1Session
from typing import Tuple

from db import fetch_twitter_info, update_tweets, upsert_twitter_info

JSON_HEADER = {"Content-Type": "application/json"}
DOMAIN_URL = "https://hacku-techlion.herokuapp.com"
LOGIN_URL = DOMAIN_URL + "/twitter/login"
TIMELINE_EP = "https://api.twitter.com/1.1/statuses/user_timeline.json"
TOP_URL = "https://hacku-techlion.herokuapp.com/dummy"
CALLBACK_URL = "https://hacku-techlion.herokuapp.com/twitter/oauth-callback"
REQUEST_TOKEN_EP = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_EP = "https://api.twitter.com/oauth/authorize"
ACCESS_TOKEN_EP = "https://api.twitter.com/oauth/access_token"
VERIFY_EP = "https://api.twitter.com/1.1/account/verify_credentials.json"

CK = os.environ.get("CONSUMER_API_KEY")
CS = os.environ.get("CONSUMER_API_SECRET_KEY")


def json_response(status_code: int, body: dict) -> HTTPResponse:
    return HTTPResponse(status=status_code, body=json.dumps(body, ensure_ascii=False), headers=JSON_HEADER)


def get_new_tweets(oauth: OAuth1Session, latest: int) -> Tuple[Response, list]:
    q = {"since_id": latest} if latest is not None else {"count": 200}
    req = oauth.get(TIMELINE_EP, params=q)
    if req.status_code != 200:
        return req, []
    tweets = []
    for tw in req.json():
        created_at = datetime.strptime(tw["created_at"], "%a %b %d %H:%M:%S %z %Y").astimezone(timezone("Asia/Tokyo"))
        today = datetime.now(tz=timezone("Asia/Tokyo")).date()
        if created_at.date() == today:
            tweets.append({
                "id": tw["id"],
                "text": tw["text"],
                "hashtags": [tag["text"] for tag in tw["entities"]["hashtags"]],
                "media": [media["media_url_https"] for media in
                          tw.get("extended_entities", dict()).get("media", list())],
                "url": f"https://twitter.com/{tw['user']['screen_name']}/status/{tw['id']}",
                "created_at": {
                    "year": created_at.year,
                    "month": created_at.month,
                    "day": created_at.day,
                    "hour": created_at.hour,
                    "minute": created_at.minute,
                    "second": created_at.second
                }
            })
        else:
            break
    return req, tweets


@get("/twitter/today/<user_id>")
def get_twitter_today(user_id: str) -> HTTPResponse:
    twitter = fetch_twitter_info(user_id)
    if twitter is None:
        body = {"error": {
            "message": f"User {user_id} does not exist.",
            "callback_url": LOGIN_URL
        }}
        return json_response(404, body)
    if twitter["twitter_id"] is None:
        body = {"error": {
            "message": f"User {user_id} is not linked to Twitter account.",
            "callback_url": LOGIN_URL
        }}
        return json_response(403, body)
    oauth = OAuth1Session(CK, CS, twitter["twitter_access_token"], twitter["twitter_access_token_secret"])
    res, new_tweets = get_new_tweets(oauth, twitter["twitter_latest_id"])
    if res.status_code == 401 and res.json()["errors"][0]["code"] == 89:
        body = {"error": {
            "message": "The registered token is invalid. It may have expired.",
            "callback_url": LOGIN_URL
        }}
        return json_response(401, body)
    elif res.status_code != 200:
        return json_response(res.status_code, res.json())
    body = update_tweets(user_id, new_tweets)
    return json_response(200, body)


@get("/twitter/login")
def twitter_login():
    CALLBACK_URL = "http://0.0.0.0:5000/twitter/oauth-callback"
    TOP_URL = "http://0.0.0.0:5000/dummy"
    callback_query = "?callback=" + request.params.get("callback", TOP_URL)
    oauth_session = OAuth1Session(client_key=CK, client_secret=CS, callback_uri=CALLBACK_URL + callback_query)
    oauth_session.fetch_request_token(REQUEST_TOKEN_EP)
    authorization_url = oauth_session.authorization_url(AUTHORIZE_EP)
    return redirect(authorization_url)


@get("/twitter/oauth-callback")
def twitter_oauth_callback():
    oauth_session = OAuth1Session(CK, CS)
    oauth_session.parse_authorization_response(request.url)
    token = oauth_session.fetch_access_token(ACCESS_TOKEN_EP)
    oauth = OAuth1Session(CK, CS, token["oauth_token"], token["oauth_token_secret"])
    req = oauth.get(VERIFY_EP)
    if req.status_code != 200:
        return json_response(req.status_code, req.json())
    user = req.json()
    upsert_twitter_info(user["id"], user["screen_name"], token["oauth_token"], token["oauth_token_secret"])
    return redirect(f"{request.params.get('callback')}?your_user_id={user['id']}")
