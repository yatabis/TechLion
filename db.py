from datetime import datetime
import json
import os
import psycopg2
from psycopg2.extras import DictCursor
from typing import Optional

DSN = os.environ.get("DATABASE_URL")


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
    return dict(twitter_info) if twitter_info is not None else None


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
                        (user_id, user_id, user_name, access_token, access_secret,
                         user_name, access_token, access_secret))


def test():
    gmail = "39yatabis.rim8820xxx@gmail.com"
    with open_pg() as conn:
        with open_cursor(conn) as cur:
            cur.execute("insert into users (user_id, google_id) values (%s, %s)", (gmail, gmail))
        conn.commit()


if __name__ == '__main__':
    # from pprint import pprint
    # twitter = fetch_twitter_info("yatabis_tg")
    # print(twitter)
    # tw = fetch_tweets("yatabis_tg", "20190826")
    # pprint(tw)
    upsert_twitter_info(19276,
                        "JehanneAI",
                        "3119715565-OFY6fMMSsGv2iGPpRV07azTjDOxkHbyRJRO3ZgK",
                        "AOxoVvCwKHnev3n67PbI7z2Qkk3c3aoVifgKIcSNAvX9Q")
