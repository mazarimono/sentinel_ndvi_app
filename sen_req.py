import urllib.request
from datetime import date, timedelta

import pandas as pd
import requests


def _gen_token(client_id, client_secret):
    base_path = "https://www.arcgis.com/sharing/rest/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    r = requests.get(base_path, params=params)
    token = r.json()["access_token"]
    return token


def _get_sentinel_data(arcgis_token, field_center, satellite_date):
    base_path = "https://sentinel.arcgis.com/arcgis/rest/services/Sentinel2/ImageServer/getSamples"
    params = urllib.parse.urlencode(
        {
            "geometryType": "esriGeometryMultiPoint",
            "geometry": {"points": field_center, "spatialReference": {"wkid": 4326}},
            "mosaicRule": {
                "mosaicMethod": "esriMosaicAttribute",
                "where": "category = 1 AND cloudcover <= 0.10",
                "sortField": "acquisitionDate",
                "sortValue": satellite_date,
                "ascending": "true",
            },
            "token": arcgis_token,
            "returnFirstValueOnly": "true",
            "f": "json",
        }
    )

    r = requests.get(base_path, params=params)
    data = r.json()
    return data


def get_from_sentinel(client_id, client_secret, field_center, satellite_date):

    arcgis_token = _gen_token(client_id, client_secret)
    sample_data = _get_sentinel_data(arcgis_token, field_center, satellite_date)
    band_data = sample_data["samples"][0]["value"].split(" ")
    band_data = map((lambda x: int(x)), band_data)
    df = pd.DataFrame(band_data).T
    df.index = [satellite_date]
    df.columns = [
        "band1",
        "band2",
        "band3",
        "band4",
        "band5",
        "band6",
        "band7",
        "band8",
        "band8a",
        "band9",
        "band10",
        "band11",
        "band12",
    ]
    df["NDVI"] = (df["band8"] - df["band4"]) / (df["band8"] + df["band4"])
    return df


def make_graph_data(df):
    df = df[["NDVI"]]
    df = df.reset_index()
    return df


def make_date():
    today = date.today()
    date_box = []
    for i in range(17):
        new_date = today - timedelta(28) * i
        new_date = f"{new_date.year}-{new_date.month}-{new_date.day}"
        date_box.append(new_date)
    return date_box
