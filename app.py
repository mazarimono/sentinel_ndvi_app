import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State

import sen_req

arc_pass = {
    "ClientID": yourID,
    "ClientSecret": YourSecret,
}
# つくば市
# 緯度　36.0835 ; lat,　経度 140.0764 ; lon


button_input_style = {"height": 40, "margin": "1%"}
half_style = {"width": "43%", "margin": "1%", "display": "inline-block", "verticalAlign": "top"}

app = dash.Dash(__name__)


app.layout = html.Div(
    [
        html.H1("Sentinel NDVI FDNR"),
        html.Div(
            [
                dcc.Input(
                    placeholder="経度を入力してください",
                    id="get_lat",
                    type="number",
                    style=button_input_style,
                ),
                dcc.Input(
                    placeholder="緯度を入力してください",
                    id="get_lon",
                    type="number",
                    style=button_input_style,
                ),
                html.Button(
                    id="cal_button",
                    children="経度緯度入力",
                    n_clicks=0,
                    style=button_input_style,
                ),
            ]
        ),
        html.Div(
            [
                dcc.Loading([
                html.Div([dcc.Graph(id="graph")], style=half_style),
                html.Div(id="table", style=half_style),
                ], type="graph"),
            ]
        ),
    ],
    style={"padding": "2%"},
)


@app.callback(
    [Output("graph", "figure"), Output("table", "children")],
    [Input("cal_button", "n_clicks")],
    [State("get_lat", "value"), State("get_lon", "value")],
    prevent_initial_call=True,
)
def update_data(n_clicks, lat_input, lon_input):

    if lat_input and lon_input:

        
        # 入力より位置データを作成
        field_center = [[lat_input, lon_input]]
        # 日付はまずは、13か月分を取得するようにするどのように作るか？
        date_box = sen_req.make_date()

        dff = pd.DataFrame()

        for d in date_box:

            data = sen_req.get_from_sentinel(arc_pass["ClientID"], arc_pass["ClientSecret"], field_center, d)
            dff = pd.concat([dff, data])

        dff = sen_req.make_graph_data(dff)
        dff = dff.sort_index(ascending=False)

        my_graph = px.line(dff, x="index", y="NDVI")
        my_table = dash_table.DataTable(
            columns=[{"name":i, "id":i} for i in dff.columns],
            data = dff.to_dict("records")
        )
        return my_graph, my_table


if __name__ == "__main__":
    app.run_server(debug=True, host=(0, 0, 0, 0))
