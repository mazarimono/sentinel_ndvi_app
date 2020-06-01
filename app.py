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
    "ClientID": user_id,
    "ClientSecret": user_secret,
}
# つくば市
# 緯度　36.0835 ; lat,　経度 140.0764 ; lon

"""
経度緯度からAPIをたたき、それを可視化するアプリケーション。
"""


button_input_style = {"height": 40, "margin": "1%"}
half_style = {"width": "43%", "margin": "1%", "display": "inline-block", "verticalAlign": "top"}

app = dash.Dash(__name__)


app.layout = html.Div(
    [
        html.H1("Sentinel NDVI FDNR"),

        dcc.Store("session_storage", storage_type="memory"),

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
                html.Div([dcc.Graph(id = "show_graph")],
                style=half_style),
                ], type="graph"),
            ]
        ),
        html.Div([
            html.H2("取得データ"),
            dcc.Loading([
                html.Div(id="table"
                )
            ], type="graph")
        ], style={"padding": "5%"}),
    ],
    style={"padding": "2%"},
)


@app.callback(
    [Output("graph", "figure"), Output("table", "children"), Output("session_storage", "data")],
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

        dff = sen_req.get_from_sentinel(arc_pass["ClientID"], arc_pass["ClientSecret"], field_center, date_box)
        dff = dff.sort_index(ascending=True)
        dff = dff.reset_index()
        
        my_graph = px.line(dff, x="index", y="NDVI")
        my_table = dash_table.DataTable(
            columns=[{"name":i, "id":i} for i in dff.columns],
            data = dff.to_dict("records"),
            style_table={"overflowX": 'auto', "minWidth": '100%'},
            fixed_columns={'headers': True, 'data': 1},
            export_format="csv"
        )
        dff_dict = dff.to_dict('records')

        return my_graph,my_table,dff_dict

@app.callback(Output("show_graph", "figure"), [Input("session_storage", "data")],prevent_initial_call=True)
def use_storage(data):
    df = pd.DataFrame(data)
    df = df.iloc[:,:14]
    df_melt = df.melt(id_vars="index")
    return px.line(df_melt, x="index", y="value", color="variable")


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
