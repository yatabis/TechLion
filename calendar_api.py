import os
from bottle import get, request, redirect
from requests_oauthlib import OAuth2Session

REDIRECT_URI = "https://hacku-techlion.herokuapp.com/google/oauth-callback"
TOP_URL = "https://hacku-techlion.herokuapp.com/dummy"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = ["https://www.googleapis.com/auth/calendar.readonly",
         "https://www.googleapis.com/oauth2/v1/userinfo"]

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
    return dict(token)
