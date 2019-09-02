from datetime import datetime, timedelta
import json
import os
from bottle import route, request, redirect, static_file, template
from bottle import HTTPResponse
import googlemaps
from pytz import timezone
import requests
from requests_oauthlib import OAuth2Session
from typing import Tuple, Optional

from http_elements import post_validation, json_response, JSON_HEADER, Error
from db import link_google_account, fetch_google_token, refresh_token

AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = ["https://www.googleapis.com/auth/calendar.readonly",
         "https://www.googleapis.com/auth/userinfo.profile",
         "https://www.googleapis.com/auth/userinfo.email"]
VERIFY_EP = "https://www.googleapis.com/oauth2/v1/userinfo"
REFRESH_EP = "https://www.googleapis.com/oauth2/v4/token"
CALENDAR_EP = "https://www.googleapis.com/calendar/v3/calendars/"

REDIRECT_URL = os.environ.get("GOOGLE_REDIRECT_URL")
SUCCESS_URL = os.environ.get("SUCCESS_URL")
ERROR_URL = "https://hacku-techlion.herokuapp.com/google/error"
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
MAP_API_KEY = os.environ.get("MAP_API_KEY")
PASSWORD = os.environ.get("PASSWORD")
PHOTO_WIDTH = 800


def datetime_object(dt: str) -> dict:
    date_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone("Asia/Tokyo"))
    return {
        "year": date_time.year,
        "month": date_time.month,
        "day": date_time.day,
        "hour": date_time.hour,
        "minute": date_time.minute,
        "second": date_time.second,
    }


def refresh_token_flow(user: str, token: str) -> Tuple[dict, Optional[Error]]:
    data = {
        "refresh_token": token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    req = requests.post(REFRESH_EP, data=json.dumps(data).encode("utf-8"), headers=JSON_HEADER)
    result = req.json()
    if req.status_code != 200:
        return {}, Error(req.status_code, result)
    return refresh_token(user, result["access_token"], result["expires_in"])


@route("/google/events/today")
def get_events_today() -> HTTPResponse:
    user = request.get_cookie("user_id", secret=PASSWORD)
    if user is None:
        return Error(400, "parameter `user` is required").response
    token, err = fetch_google_token(user)
    if err:
        return err.response
    if float(token.get("expires_at")) < datetime.now().timestamp():
        token, err = refresh_token_flow(user, token.get("refresh_token"))
        if err:
            return err.response
    today = datetime.now(timezone("Asia/Tokyo")).date()
    params = {
        "orderBy": "startTime",
        "singleEvents": True,
        "timeMin": datetime(today.year, today.month, today.day, 0, 0, 0, 0, timezone("Asia/Tokyo")).isoformat(),
        "timeMax": datetime(today.year, today.month, today.day + 1, 0, 0, 0, 0, timezone("Asia/Tokyo")).isoformat()
    }
    header = {"Authorization": f"Bearer {token['access_token']}"}
    req = requests.get(CALENDAR_EP + token["id"] + "/events", params=params, headers=header)
    if req.status_code != 200:
        return json_response(req.status_code, req.json())
    result = req.json().get("items")
    body = []
    for item in result:
        location = item.get("location")
        body.append({
            "title": item.get("summary"),
            "start": datetime_object(item.get("start", {}).get("dateTime")),
            "end": datetime_object(item.get("end", {}).get("dateTime")),
            "location": {
                "name": location
            },
            "link": item.get("htmlLink"),
        })
        if location is not None:
            map_info, err = get_map(location)
            if err is None:
                body[-1]["location"]["photo"] = map_info["photo_url"]
                body[-1]["location"]["latitude"] = map_info["latitude"]
                body[-1]["location"]["longitude"] = map_info["longitude"]
    return json_response(200, body)


def get_map(q: str) -> Tuple[dict, Optional[Error]]:
    if q == "":
        return {}, Error(400, "parameter `q` is required.")
    client = googlemaps.Client(key=MAP_API_KEY)
    req = client.places(q)
    if req['status'] != 'OK':
        return {}, Error(400, f"Google Maps API returns `{req['status']}`")
    if len(req["results"]) != 1:
        return {}, Error(500, f"Invalid number of result ({len(req['results'])}) are returned.")
    result = req["results"][0]
    body = {}
    photos = result.get("photos")
    if photos:
        body["photo_url"] = (f"https://maps.googleapis.com/maps/api/place/photo"
                             f"?maxwidth={PHOTO_WIDTH}"
                             f"&photoreference={photos[0]['photo_reference']}"
                             f"&key={MAP_API_KEY}")
    body["latitude"] = result["geometry"]["location"]["lat"]
    body["longitude"] = result["geometry"]["location"]["lng"]
    return body, None


@route("/google/login", method=["GET", "POST"])
def google_login():
    *_, err = post_validation(request)
    if err:
        return err.response
    oauth = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL, scope=SCOPE)
    authorization_url, state = oauth.authorization_url(AUTH_URI,
                                                       access_type="offline", approval_prompt="force")
    return redirect(authorization_url)


@route("/google/oauth-callback")
def google_oauth_callback():
    oauth = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URL)
    token = oauth.fetch_token(token_url=TOKEN_URI, authorization_response=request.url, client_secret=CLIENT_SECRET)
    req = oauth.get(VERIFY_EP, headers={"Authorization": f"Bearer {token['access_token']}"})
    if req.status_code != 200:
        return json_response(req.status_code, req.json())
    google = req.json()
    user, err = link_google_account(google["email"],
                                    token["access_token"],
                                    token.get("refresh_token"),
                                    token["expires_at"])
    if err:
        return redirect(f"{ERROR_URL}?code={err.code}&message={err.message}")
    # if user["twitter_id"] is None:
    #     return redirect("https://hacku-techlion.herokuapp.com/twitter/login")
    return template(SUCCESS_URL)


@route("/google/error", method=["GET"])
def login_error():
    params = request.params
    message = f"{params.get('code', '')}: {params.get('message', '')}"
    return template("template/login_error.html", social="Google", message=message)


@route("/static/img/btn_google_signin_dark_normal_web.png", method=["GET"])
def google_login_button():
    return static_file("img/btn_google_signin_dark_normal_web.png", __file__.rsplit("/", 1)[0] + "/static")
