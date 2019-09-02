import json
import os
from bottle import HTTPResponse, BaseRequest
from typing import Dict, List, Tuple, Optional

JSON_HEADER = {"Content-Type": "application/json"}
PASSWORD = os.environ.get("PASSWORD")


class Error:
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        self.body = {"error": {
            "code": code,
            "message": message
        }}
        self.response = HTTPResponse(status=code,
                                     body=json.dumps(self.body, ensure_ascii=False),
                                     headers={"Content-Type": "application/json"})


def get_validation(req: BaseRequest, *args) -> Tuple[Optional[str], Optional[Error]]:
    if req.method != "GET":
        return "", Error(405, "POST method is not allowed.")
    return (*[req.params.get(k) for k in args], None)


def post_validation(req: BaseRequest, *args) -> Tuple[dict, Optional[Error]]:
    if req.method != "POST":
        return {}, Error(405, "GET method is not allowed.")
    if req.get_header("Content-Type") != "application/json":
        return {}, Error(400, "HTTP request header `Content-Type` must be `application/json`.")
    if req.body.getvalue().decode() == "":
        return {}, Error(400, "Request body is empty.")
    for k in args:
        if not req.json.get(k):
            return {}, Error(400, f"The field {k} does not exist in the request body.")
    return req.json, None


def json_response(status_code: int, body: dict, cookie: str = None) -> HTTPResponse:
    response = HTTPResponse(status=status_code, body=json.dumps(body, ensure_ascii=False))
    response.set_header("Content-Type", "application/json")
    if cookie is not None:
        response.set_cookie("user_id", cookie, secret=PASSWORD, max_age=60*60*24*7)
    return response
