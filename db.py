from datetime import datetime
import json
import os
import psycopg2
from psycopg2.extras import DictCursor
from typing import Optional

from cryptograph import encrypt, decrypt

DSN = os.environ.get("DATABASE_URL")
PASSWORD = os.environ.get("PASSWORD")


def open_pg():
    return psycopg2.connect(DSN)


def open_cursor(conn):
    return conn.cursor(cursor_factory=DictCursor)


def fetch_twitter_info(user_id: str) -> Optional[list]:
    with open_pg() as conn:
        with open_cursor(conn) as cur:
            cur.execute("select twitter_id,"
                        "       twitter_name,"
                        "       twitter_access_token,"
                        "       twitter_access_token_secret,"
                        "       twitter_latest_id "
                        "from   users "
                        "where  user_id = %s",
                        (user_id,))
            twitter_info = cur.fetchone()
    if twitter_info is None:
        return None
    twitter_info = dict(twitter_info)
    twitter_info["twitter_access_token"] = decrypt(twitter_info["twitter_access_token"], PASSWORD)
    twitter_info["twitter_access_token_secret"] = decrypt(twitter_info["twitter_access_token_secret"], PASSWORD)
    return twitter_info


def fetch_tweets(user_id: str, date: str = None) -> list:
    if date is None:
        date = datetime.today().strftime("%Y%m%d")
    with open_pg() as conn:
        with open_cursor(conn) as cur:
            cur.execute("select tweets "
                        "from   diary "
                        "where  user_id = %s"
                        "   and date = %s",
                        (user_id, date))
            tweets = cur.fetchone()
            if tweets is None:
                cur.execute("insert into diary "
                            "(user_id, date) "
                            "values (%s, %s)",
                            (user_id, date))
    return json.loads(tweets[0]) if tweets is not None else []


def update_tweets(user_id: str, new_tweets: list, date: str = None) -> list:
    if date is None:
        date = datetime.today().strftime("%Y%m%d")
    now_tweets = fetch_tweets(user_id, date) + new_tweets[::-1]
    if len(new_tweets) > 0:
        latest = new_tweets[0]["id"]
        with open_pg() as conn:
            with open_cursor(conn) as cur:
                cur.execute("update diary "
                            "set    tweets = %s "
                            "where  user_id = %s"
                            "   and date = %s",
                            (json.dumps(now_tweets, ensure_ascii=False), user_id, date))
                cur.execute("update users "
                            "set    twitter_latest_id = %s "
                            "where  user_id = %s",
                            (latest, user_id))
    return now_tweets


def fetch_google_token(user_id: str):
    with open_pg() as conn:
        with open_cursor(conn) as cur:
            cur.execute("select google_access_toke, google_refresh_token, google_token_expires_at "
                        "from   users "
                        "where  user_id = %s",
                        (user_id,))
            token = cur.fetchone()
    return dict(token) if token is not None else None


def upsert_twitter_info(user_id, user_name, access_token, access_secret):
    access_token_aes = encrypt(access_token, PASSWORD)
    access_secret_aes = encrypt(access_secret, PASSWORD)
    with open_pg() as conn:
        with open_cursor(conn) as cur:
            cur.execute("insert into users "
                        "(user_id, twitter_id, twitter_name, twitter_access_token, twitter_access_token_secret)"
                        "values (%s, %s, %s, %s, %s) "
                        "on conflict (twitter_id)"
                        "do update set "
                        "twitter_name = %s,"
                        "twitter_access_token = %s,"
                        "twitter_access_token_secret = %s",
                        (user_id, user_id, user_name, access_token_aes, access_secret_aes,
                         user_name, access_token_aes, access_secret_aes))
