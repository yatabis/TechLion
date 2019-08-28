import os
from bottle import get, request, redirect
from requests_oauthlib import OAuth2Session

from db import upsert_google_info

REDIRECT_URI = "https://hacku-techlion.herokuapp.com/google/oauth-callback"
TOP_URL = "https://hacku-techlion.herokuapp.com/dummy"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = ["https://www.googleapis.com/auth/calendar.readonly",
         "https://www.googleapis.com/auth/userinfo.profile",
         "https://www.googleapis.com/auth/userinfo.email"]
VERIFY_EP = "https://www.googleapis.com/oauth2/v1/userinfo"

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


@get("/google/login")
def google_login():
    # REDIRECT_URI = "http://localhost:5000/google/oauth-callback"
    callback_query = "?callback=" + request.params.get("callback", TOP_URL)
    oauth = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI + callback_query, scope=SCOPE)
    authorization_url, state = oauth.authorization_url(AUTH_URI, access_type="offline", prompt="select_account")
    return redirect(authorization_url)


@get("/google/oauth-callback")
def google_oauth_callback():
    callback_query = "?callback=" + request.params.get("callback")
    oauth = OAuth2Session(client_id=CLIENT_ID, redirect_uri=REDIRECT_URI + callback_query)
    token = oauth.fetch_token(token_url=TOKEN_URI, authorization_response=request.url, client_secret=CLIENT_SECRET)
    req = oauth.get(ep, headers={"Authorization": f"Bearer {token['access_token']}"})
    if req.status_code != 200:
        return json_response(req.status_code, req.json())
    user = req.json()
    user_id = user["email"].split("@")[0]
    upsert_google_info(user_id, user["email"], token["access_token"], token["refresh_token"], token["expires_at"])
    return redirect(f"{request.params.get('callback')}?your_user_id={user_id}")
