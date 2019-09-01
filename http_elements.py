import json
from bottle import HTTPResponse, BaseRequest
from typing import Dict, Tuple, Optional

JSON_HEADER = {"Content-Type": "application/json"}


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


def get_validation(req: BaseRequest, *args) -> Tuple[dict, Optional[Error]]:
    if req.method != "GET":
        return {}, Error(405, "POST method is not allowed.")
    if req.get_header("Content-Type") != "application/json":
        return {}, Error(400, "HTTP request header `Content-Type` must be `application/json`.")
    if args and req.body.getvalue().decode() == "":
        return {}, Error(400, "Request body is empty.")
    for k in args:
        if not req.json.get(k):
            return {}, Error(400, f"The field {k} does not exist in the request body.")
    return req.json, None


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


def json_response(status_code: int, body: dict) -> HTTPResponse:
    return HTTPResponse(status=status_code, body=json.dumps(body, ensure_ascii=False), headers=JSON_HEADER)
