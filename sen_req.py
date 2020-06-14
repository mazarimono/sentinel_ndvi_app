import urllib.request
from datetime import date, timedelta
import time 

import pandas as pd
import requests

# ID, SECRETからトークンを生成する
def gen_token(client_id, client_secret):
    base_path = "https://www.arcgis.com/sharing/rest/oauth2/token"
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }

    r = requests.get(base_path, params=params)
    token = r.json()["access_token"]
    return token

# センチネルのAPIからサンプルデータを取得する
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

# センチネルAPIからデータを取得し、データフレーム化する。
def get_from_sentinel(arcgis_token, field_center, satellite_date):
    """
    センチネルAPIからデータを取得し、データフレーム化する
    今のところ、15カ月分くらいの日付文を
    field_centerは[[緯度, 経度]]の形で入力
    satellite_dateは["YYYY-MM-DD"]の形
    """
    
    dff = pd.DataFrame()

    for d in satellite_date:
        sample_data = _get_sentinel_data(arcgis_token, field_center, d)
        band_data = sample_data["samples"][0]["value"].split(" ")
        band_data = map((lambda x: int(x)), band_data)
        df = pd.DataFrame(band_data).T
        df.index = [d]
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
        # バンドデータ以外の取得
        return_location_data_x = sample_data["samples"][0]["location"]["x"] # 返り値X
        return_location_data_y = sample_data["samples"][0]["location"]["y"] # 返り値X
        raster_id = sample_data["samples"][0]["rasterId"]
        resolution = sample_data["samples"][0]["resolution"]
        location_id = sample_data["samples"][0]["locationId"]
        field_center_x = field_center[0][0]
        field_center_y = field_center[0][1]

        df["返り値x"] = return_location_data_x
        df["返り値y"] = return_location_data_y 
        df["RasterID"] = raster_id 
        df["resolution"] = resolution 
        df["locationID"] = location_id 
        df["要求x"] = field_center_x
        df["要求y"] = field_center_y 

        dff = pd.concat([dff, df])
    
    dff.index = pd.to_datetime(dff.index)
    dff = dff.sort_index(ascending=True)
    dff = dff.reset_index()
    
    return dff


def make_graph_data(df):
    """
    コラムにデータの種類を持つデータフレームを引数に渡すと、
    NDVI値のみのデータフレーム作成
    """
    df = df[["NDVI"]]
    df = df.reset_index()
    return df


def make_date(days=28):
    """
    当日を基準に、daysずつ日付を前に戻って
    作成する。初期設定は28日。
    15カ月分くらい作成される(480日)
    """
    today = date.today()
    step_num = 480 // days
    date_box = []
    for i in range(step_num):
        new_date = today - timedelta(days) * i
        new_date = f"{new_date.year}-{new_date.month}-{new_date.day}"
        date_box.append(new_date)
    return date_box

# 7日刻みでデータを取得すると420秒
# 28日刻みだと22秒
# 14日だと63秒