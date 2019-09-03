from datetime import datetime
import json
import os
from bottle import route, request, redirect, static_file, template
from bottle import HTTPResponse
from pytz import timezone
import requests
from requests_oauthlib import OAuth1Session
from typing import Tuple

from http_elements import get_validation, post_validation, json_response, Error
from db import fetch_twitter_info, update_tweets, link_twitter_account

DOMAIN_URL = "https://hacku-techlion.herokuapp.com"
LOGIN_URL = DOMAIN_URL + "/twitter/login"
TIMELINE_EP = "https://api.twitter.com/1.1/statuses/user_timeline.json"
REQUEST_TOKEN_EP = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_EP = "https://api.twitter.com/oauth/authorize"
ACCESS_TOKEN_EP = "https://api.twitter.com/oauth/access_token"
VERIFY_EP = "https://api.twitter.com/1.1/account/verify_credentials.json"

CALLBACK_URL = os.environ.get("TWITTER_CALLBACK_URL")
SUCCESS_URL = os.environ.get("SUCCESS_URL")
ERROR_URL = os.environ.get("TWITTER_ERROR_URL")
CK = os.environ.get("CONSUMER_API_KEY")
CS = os.environ.get("CONSUMER_API_SECRET_KEY")
PASSWORD = os.environ.get("PASSWORD")

MORNING = ["おは", "お早う", "おはやう", "おきた", "起きた"]
NIGHT = ["おやすみ", "お休み", "ねる", "寝る", "ねます", "寝ます"]
BREAKFAST = ["あさごはん", "朝ごはん", "あさご飯", "朝ご飯", "朝飯", "朝食", "朝メシ"]
LUNCH = ["ひるごはん", "昼ごはん", "ひるご飯", "昼ご飯", "昼飯", "昼メシ", "昼食"]
DINNER = ["ばんごはん", "晩ごはん", "晩ご飯", "晩御飯", "夕ご飯", "夜ご飯", "晩飯", "夕食", "夕飯"]


def get_new_tweets(oauth: OAuth1Session, latest: int) -> Tuple[requests.Response, list]:
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


@route("/twitter/today", method=["GET", "POST"])
def get_twitter_today() -> HTTPResponse:
    user = request.get_cookie("user_id")  # , secret=PASSWORD)
    q = request.params.q
    *_, err = get_validation(request)
    if err:
        return err.response
    if user is None:
        return Error(400, "parameter `user` is required").response
    twitter, err = fetch_twitter_info(user)
    if err:
        return err.response
    oauth = OAuth1Session(CK, CS, twitter["access_token"], twitter["access_secret"])
    res, new_tweets = get_new_tweets(oauth, twitter["latest_id"])
    if res.status_code == 401 and res.json()["errors"][0]["code"] == 89:
        return Error(401, "The registered token is invalid. It may have expired. Please re-login.").response
    elif res.status_code != 200:
        return json_response(res.status_code, res.json())
    body = update_tweets(user, new_tweets)
    if q is not None:
        body = [b for b in body if q in b["text"]]
    return json_response(200, body)


@route("/twitter/today/detail", method=["GET", "POST"])
def get_twitter_today_detail() -> HTTPResponse:
    user = request.get_cookie("user_id")  # , secret=PASSWORD)
    q = request.params.q
    *_, err = get_validation(request)
    if err:
        return err.response
    if user is None:
        return Error(400, "parameter `user` is required").response()
    twitter, err = fetch_twitter_info(user)
    if err:
        return err.response
    oauth = OAuth1Session(CK, CS, twitter["access_token"], twitter["access_secret"])
    res, new_tweets = get_new_tweets(oauth, twitter["latest_id"])
    if res.status_code == 401 and res.json()["errors"][0]["code"] == 89:
        return Error(401, "The registered token is invalid. It may have expired. Please re-login.").response
    elif res.status_code != 200:
        return json_response(res.status_code, res.json())
    body = update_tweets(user, new_tweets)
    hashtags = list(set(hstg for tw in body for hstg in tw["hashtags"]))
    detail = {
        "event": [],
        "morning": [],
        "breakfast": [],
        "lunch": [],
        "dinner": [],
        "night": []
    }
    for h in sorted(hashtags):
        detail[h] = []
    detail["other"] = []
    used = set()
    for idx, tw in enumerate(body):
        if sum([t in tw["text"] for t in MORNING]) > 0:
            detail["morning"].append(tw)
            used.add(idx)
        if sum([t in tw["text"] for t in NIGHT]) > 0:
            detail["night"].append(tw)
            used.add(idx)
        if sum([t in tw["text"] for t in BREAKFAST]) > 0:
            detail["breakfast"].append(tw)
            used.add(idx)
        if sum([t in tw["text"] for t in LUNCH]) > 0:
            detail["lunch"].append(tw)
            used.add(idx)
        if sum([t in tw["text"] for t in DINNER]) > 0:
            detail["dinner"].append(tw)
            used.add(idx)
        if len(tw["hashtags"]) > 0:
            for hs in tw["hashtags"]:
                detail[hs].append(tw)
                used.add(idx)
        if idx not in used:
            detail["other"].append(tw)
    if q != "":
        detail = detail.get(q, {})
    return json_response(200, detail)


@route("/twitter/login", method=["GET", "POST"])
def twitter_login():
    *_, err = post_validation(request)
    if err:
        return err.response
    oauth_session = OAuth1Session(client_key=CK, client_secret=CS, callback_uri=CALLBACK_URL)
    oauth_session.fetch_request_token(REQUEST_TOKEN_EP)
    authorization_url = oauth_session.authorization_url(AUTHORIZE_EP)
    return redirect(authorization_url)


@route("/twitter/oauth-callback")
def twitter_oauth_callback():
    oauth_session = OAuth1Session(CK, CS)
    oauth_session.parse_authorization_response(request.url)
    token = oauth_session.fetch_access_token(ACCESS_TOKEN_EP)
    oauth = OAuth1Session(CK, CS, token["oauth_token"], token["oauth_token_secret"])
    req = oauth.get(VERIFY_EP)
    if req.status_code != 200:
        return json_response(req.status_code, req.json())
    twitter = req.json()
    user, err = link_twitter_account(twitter["id_str"],
                                     twitter["screen_name"],
                                     token["oauth_token"],
                                     token["oauth_token_secret"])
    if err:
        return redirect(f"{ERROR_URL}?code={err.code}&message={err.message}")
    # if user["google_id"] is None:
    #     return redirect("https://hacku-techlion.herokuapp.com/twitter/login")
    return template(SUCCESS_URL)


@route("/twitter/error", method=["GET"])
def login_error():
    params = request.params
    message = f"{params.get('code', '')}: {params.get('message', '')}"
    return template("template/login_error.html", social="Twitter", message=message)


@route("/static/img/Twitter_Logo_WhiteOnBlue.svg", method=["GET"])
def google_login_button():
    return static_file("img/Twitter_Logo_WhiteOnBlue.svg", __file__.rsplit("/", 1)[0] + "/static")
