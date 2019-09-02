import os
from bottle import route, request, redirect, static_file, template
from requests_oauthlib import OAuth2Session

from http_elements import post_validation
from db import link_google_account

AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = ["https://www.googleapis.com/auth/calendar.readonly",
         "https://www.googleapis.com/auth/userinfo.profile",
         "https://www.googleapis.com/auth/userinfo.email"]
VERIFY_EP = "https://www.googleapis.com/oauth2/v1/userinfo"

REDIRECT_URL = os.environ.get("GOOGLE_REDIRECT_URL")
SUCCESS_URL = os.environ.get("SUCCESS_URL")
ERROR_URL = "https://hacku-techlion.herokuapp.com/google/error"
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


@route("/google/login", method=["GET", "POST"])
def google_login():
    user, err = post_validation(request, "user")
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
