from datetime import datetime
import json
import os
from pprint import pformat
from bottle import get, post, run, request
from bottle import HTTPResponse
import psycopg2
from psycopg2.extras import DictCursor
from pytz import timezone
from requests import Response
from requests_oauthlib import OAuth1Session

from typing import Dict, List, Tuple, Optional

DSN = os.environ.get("DATABASE_URL")

CK = os.environ.get("CONSUMER_API_KEY")
CS = os.environ.get("CONSUMER_API_SECRET_KEY")
AT = os.environ.get("ACCESS_TOKEN")
AS = os.environ.get("ACCESS_TOKEN_SECRET")

TWEETS_EP = "https://api.twitter.com/1.1/statuses/user_timeline.json"


def open_pg():
    return psycopg2.connect(DSN)


def fetch_token(username: str) -> Optional[Dict[str, str]]:
    with open_pg() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("select twitter_access_token, twitter_access_token_secret from users where twitter_name = %s",
                        (username,))
            token = cur.fetchone()
    return dict(token) if token is not None else None


def fetch_latest(username: str) -> int:
    with open_pg() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("select latest from users where twitter_name = %s", (username,))
            latest = cur.fetchone()
    return latest[0]


def fetch_todays_tweets(username: str) -> list:
    today = datetime.today().strftime("%Y%m%d")
    with open_pg() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("select tweets from diary where twitter_name = %s and date = %s", (username, today))
            tweets = json.loads(cur.fetchone()[0])
    return tweets


def get_latest_tweets(oauth: OAuth1Session, latest: int) -> Tuple[Response, list]:
    ep = TWEETS_EP + f"?screen_name=yatabis_tg&trim_user=true"
    if latest == 0:
        ep += "&count=200"
    else:
        ep += f"&since_id={latest}"
    req = oauth.get(ep)
    if req.status_code != 200:
        return req, []
    tweets = []
    for tweet in req.json():
        created_at = datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S %z %Y").astimezone(timezone("Asia/Tokyo"))
        today = datetime.now(tz=timezone("Asia/Tokyo")).date()
        if created_at.date() == today:
            tweets.append({
                "id": tweet["id"],
                "text": tweet["text"],
                "hashtags": [tag["text"] for tag in tweet["entities"]["hashtags"]],
                "media": [media["media_url_https"] for media in tweet.get("extended_entities", dict()).get("media", list())],
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


def update_tweets(username: str, add_list: list) -> Tuple[Response, list]:
    latest_tweets = fetch_todays_tweets(username) + add_list[::-1]
    new_latest = latest_tweets[-1]["id"]
    with open_pg() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("update diary set tweets = %s", (json.dumps(latest_tweets, ensure_ascii=False),))
            cur.execute("update users set latest = %s", (new_latest,))
    conn.commit()
    return latest_tweets


@get("/")
def hello():
    return "Hi, this is TechLion's application!"


@get("/twitter/today/<username>")
def get_twitter_today(username: str) -> HTTPResponse:
    token = fetch_token(username)
    if token is None:
        status_code = 404
        body = {"error": {"message": f"User '{username}' does not exist."}}
    else:
        oauth = OAuth1Session(CK, CS, token["twitter_access_token"], token["twitter_access_token_secret"])
        latest = fetch_latest(username)
        req, tweets = get_latest_tweets(oauth, latest)
        status_code = req.status_code
        if status_code == 200:
            body = update_tweets(username, tweets)
        elif status_code == 401 and req.json()["errors"][0]["code"] == 89:
            status_code = 404
            body = {"error": {"message": f"User '{username}' does not exist."}}
        else:
            body = req.json()
    return HTTPResponse(status=status_code, body=json.dumps(body, ensure_ascii=False), headers={"Content-Type": "application/json"})


if __name__ == '__main__':
    run(host="0.0.0.0", port=os.environ.get("PORT", 5000))
