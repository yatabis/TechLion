import csv
import os
from bottle import route, request
from bottle import HTTPResponse
import googlemaps
import requests
from typing import Tuple, Optional

from http_elements import get_validation, json_response, Error

MAP_API_KEY = os.environ.get("MAP_API_KEY")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

PHOTO_WIDTH = 800  # 1~1600
WEATHER_TABLE = {}
with open("weather_table.csv") as c:
    reader = csv.reader(c)
    header = next(reader)
    for row in reader:
        WEATHER_TABLE[int(row[0])] = {k: row[i] for i, k in enumerate(header)}


@route("/map", method=["GET", "POST"])
def get_map() -> HTTPResponse:
    *_, err = get_validation(request)
    if err:
        return err.response
    q = request.params.q
    if q == "":
        return Error(400, "parameter `q` is required.").response
    client = googlemaps.Client(key=MAP_API_KEY)
    req = client.places(q)
    if req['status'] != 'OK':
        return Error(400, f"Google Maps API returns `{req['status']}`").response
    if len(req["results"]) != 1:
        return Error(500, f"Invalid number of result ({len(req['results'])}) are returned.").response
    result = req["results"][0]
    body = {}
    photos = result.get("photos")
    if photos:
        body["photo_url"] = (f"https://maps.googleapis.com/maps/api/place/photo"
                             f"?maxwidth={PHOTO_WIDTH}"
                             f"&photoreference={photos[0]['photo_reference']}")
    body["latitude"] = result["geometry"]["location"]["lat"]
    body["longitude"] = result["geometry"]["location"]["lng"]
    return json_response(200, body)


@route("/weather", method=["GET", "POST"])
def get_weather(lat: int = None, lng: int = None) -> HTTPResponse:
    if lat is None or lgn is None:
        lat, lng, err = get_validation(request, "lat", "lng")
        if err:
            return err.response
    weather_get_url = f"http://api.openweathermap.org/data/2.5/weather?APPID={WEATHER_API_KEY}&lat={lat}&lon={lng}"
    req = requests.get(weather_get_url)
    if req.status_code != 200:
        return Error(req.status_code, req.json()).response
    body = req.json()

    weather_id = body['weather'][0]['id']
    weather = WEATHER_TABLE.get(weather_id)
    return json_response(200, {
        "weather": weather["main_ja"],
        "icon_url": f"http://openweathermap.org/img/wn/{weather['icon']}@2x.png",
        "temp": int(body["main"]["temp"] - 273.15),
        "humid": body["main"]["humidity"]
    })
