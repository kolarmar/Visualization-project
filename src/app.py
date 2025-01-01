from dash import Dash, html, dcc, callback, Output, Input
from datetime import datetime
import plotly.express as px
import pandas as pd
import json
import plotly.graph_objects as go

app = Dash(__name__)

server = app.server

# ------------------------------ IMPORTING DATA -------------------------------
GEOJSON = None
COUNTRIES = None
STATS_TOTAL = None
STATS_TEMPORAL = None

def load_data():
    global GEOJSON, COUNTRIES, STATS_TOTAL, STATS_TEMPORAL
    try:
        GEOJSON = json.load(open("../dataset/imported_data/countries.json", "r"))
        COUNTRIES = pd.read_csv("../dataset/processed_data/countries.csv")
        STATS_TOTAL = pd.read_csv("../dataset/processed_data/stats_total.csv")
        STATS_TEMPORAL = pd.read_csv("../dataset/processed_data/stats_temporal.csv")
    except FileNotFoundError:
        print("Could not load data")
        raise
    except Exception:
        print("An unexpected error has occured while loading the data")
        raise
    else:
        print("Data loaded succesfully")


load_data()

# ------------------------------ GLOBAL VARIABLES -----------------------------

start_date = datetime(2020, 1, 1)
DATES = [
    (start_date.replace(year=start_date.year + i // 12, month=i % 12 + 1)
    ).strftime("%Y-%m-%d") for i in range(48)
]

date_selected = DATES[24]
map_type = "Infections"

selected_countries = {"NONE"}
map_fig = None


PRIMARY_COLOR = "#0a182e"
SECUNDARY_COLOR = "white"
TERTIARY_COLOR = "#c5daeb"

# --------------------------------- FUNCTIONS ---------------------------------

def get_map():
    selected_data = STATS_TEMPORAL[STATS_TEMPORAL["date"] == date_selected]

    selected_map = {
        "Infections": "Infections per million",
        "Deaths": "Deaths absolute",
        "Vaccinations": "Vaccinations per million"}[map_type]
    
    map_colorscale = {
        "Infections": px.colors.sequential.Reds,
        "Deaths": px.colors.sequential.Greys,
        "Vaccinations": px.colors.sequential.ice_r}[map_type]

    fig = px.choropleth(data_frame=selected_data,
        geojson=GEOJSON,
        featureidkey="properties.iso_a3",
        locations="iso_code",
        color=selected_map,
        hover_data=["Infections absolute",
                    "Deaths absolute",
                    "Vaccinations absolute"],
        projection="equirectangular",
        range_color=(0, STATS_TEMPORAL[selected_map].max() / 1.5),
        color_continuous_scale=map_colorscale,
        labels={"Infections per million": "Infections per million people",
                "Vaccinations per million": "Vaccinations per million people"}
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                      coloraxis_colorbar_x=-0.1,
                      autosize=False,
                      )

    for country in selected_countries:
        border = go.Choropleth(
            locations=[country],
            z = [1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            colorbar=None,
            showscale = False,
            hoverinfo="skip",
            marker_line_width=3,
            marker_line_color="#0079c9",
            )
        
        fig.add_traces(border)

    global map_fig
    map_fig = fig

    return fig

def get_line_chart():
    global selected_countries, date_selected

    data_for_countries = STATS_TEMPORAL[STATS_TEMPORAL["iso_code"].isin(selected_countries)] \
        .groupby("date")[["Infections per million",
                         "Deaths absolute",
                         "Vaccinations per million"]].sum().reset_index()
    fig = px.line(data_for_countries,
                  x="date",
                  y=["Infections per million",
                     "Deaths absolute",
                     "Vaccinations per million"],
                  color_discrete_sequence=["#d60000", "#000000", "#0079c9"],
                  title="Summed statistics of selection"
                  )

    fig.add_vline(
        x=date_selected,
        line_dash="dash",
        line_color="purple",
    )

    fig.update_layout(yaxis=dict(range=[0, None]),
                      legend=dict(
                            yanchor="top",
                            y=10,
                            xanchor="left",
                            x=0.01,
                            title="",
                            orientation="h"
                        ),
                        )

    return fig

def get_marks():
    marks = {
        i: {'label': date[:4] if date.endswith("-01-01") else ""}
        for i, date in enumerate(DATES)
    }

    return marks

def get_total_stats():
    global selected_countries

    country_totals = STATS_TOTAL[STATS_TOTAL["iso_code"].isin(selected_countries)] \
        [["Total infections", "Total deaths", "Total vaccinations"]].sum()

    return int(country_totals["Total infections"]), \
        int(country_totals["Total deaths"]), \
        int(country_totals["Total vaccinations"])

# ---------------------------------- LAYOUT -----------------------------------

app.layout = html.Div(
    style={
        'color': TERTIARY_COLOR,
    },
    children=[

        # ----------------------- TITLE AND DESCRIPTION -----------------------

        html.Div(id="top",
            style={'padding': '20px',
               "padding-right": "60px",
               "padding-left": "40px",
               "backgroundColor": PRIMARY_COLOR,
               "display": "flex"
            },
            children=[
                html.Div(style={
                    "display": "inline-block",
                    "width": "70%",
                    "padding-right": "50px",
                    "color": "black",
                },
                children=[
                    html.H1(children='COVID-19 Global Timeline',
                        style={'textAlign':'left',
                            "backgroundColor": PRIMARY_COLOR,
                            "margin": "0",
                            "padding": "20px",
                            "padding-left": "50px",
                            "color": "white"
                        }),
                    dcc.Dropdown(["Infections", "Deaths", "Vaccinations"],
                                "Infections",
                                id="dropdown",
                                searchable=False,
                                clearable=False
                        )
                ]),

                html.Div(style={
                    "display": "inline-block",
                    "padding": "30px"
                },
                    children=[
                    html.Span("The map below shows new Covid-19 infections per \
                            country per milion people per month. Use the dropdown on the left \
                            to switch the map to absolute deaths per country per month or new \
                            vaccinations per country per million people per month. Click on the \
                            map to select countries and their statistics along with \
                            line chart will be dispayed. Multiple countries can be \
                            selected. Click on the selected country again to deselect \
                            it. Filter the line chart by clicking on the legend. \
                            Change the date on the timeline on the bottom."
                            ),
                    html.Br(),
                    html.Span("The data ranges from January 2020 until December 2023. \
                            The dataset comes from "),
                    html.A("here ", href="https://www.kaggle.com/datasets/abdoomoh \
                        /daily-covid-19-data-2020-2024?resource=download"),
                    html.Span("and "),
                    html.A("here.", href="https://ourworldindata.org/covid-vaccinations"),
                    html.Br(),
                    html.Span("Missing data were filled with zeroes.")
                ]),
            
        ]),

        html.Div(id="middle", style={
            "display": "flex",
        },
        children=[
            # -------------------------------- MAP --------------------------------
            html.Div(id="map_div",
                style={
                    "width": "60%",
                    "height": "100%",
                    "display": "inline-block",
                    },
                children=[
                dcc.Graph(id="map_content", figure={},
                        style={"width": "100%", "height": "75vh"},
                        responsive=True),
                ]),

            html.Div(id="right_panel",
                style={
                    'backgroundColor':'white',
                    "display": "inline-flex",
                    "width": "40%",
                    "align-items": "stretch",
                },
                children=[
                    html.Div(id="right_flex",
                        style={
                            "display": "flex",
                            "flex-direction": "column",
                            "height": "100%",
                            "width": "100%",
                            "border-left": f"10px solid {PRIMARY_COLOR}"
                        },
                        children=[
                            # -------------------------- STATISTICS ---------------------------

                            html.Div(id="statistics",
                                style={
                                    'padding': '15px',
                                    "height": "50%",
                                    "color": "black",
                                    #"fontSize": "20px"
                                    },
                                children=[
                                html.H1("Country Statistics", style={
                                    "textAlign": "left",
                                    "margin-top": "0px"
                                    }),

                                dcc.Markdown(id="statistics_markdown",
                                             style={"padding-left": "50px"},
                                             children=''' '''),
                            ]),

                            # -------------------------- LINE CHART ---------------------------

                            html.Div(id="line_chart",
                                style={"flex": "1", "border-top": f"10px solid {PRIMARY_COLOR}"},
                                children=[
                                dcc.Graph(id="line_chart_content", figure={})
                            ]),
                        ]),
                ]),

        ]),

        # ----------------------------- TIMELINE ------------------------------

        html.Div(id="bottom", children=[
            html.Div(id="selected_date",
                     children=["Selected date: 2022-01-01"],
                     style={"color": "white", "margin-bottom": "10px", "margin-left": "25px"}
                     ),
            dcc.Slider(
                id="timeline_slider",
                min=0,
                max=len(DATES) - 1,
                step=1,
                value=24,
                updatemode="mouseup",
                marks=get_marks(),
                included=False,
                )
        ],
        style={
            'padding': '15px',
            "padding-bottom": "30px",
            "backgroundColor": PRIMARY_COLOR,
            "height": "70px",
            }),
    ]
)

# --------------------------------- CALLBACKS ---------------------------------

@callback(
    Output("statistics_markdown", "children"),
    Output("line_chart_content", "figure"),
    Output("map_content", "figure"),
    Input("map_content", "clickData")
)
def on_map_click(clickData):
    if clickData is None:
        return f"""
        **Selected countries:** None
        - Total infections: 0
        - Total deaths: 0
        - Total vaccinations: 0
        """, get_line_chart(), get_map()

    iso_code = clickData["points"][0]["location"]

    print(iso_code)

    global selected_countries
    if iso_code in selected_countries:
        selected_countries.remove(iso_code)
    else:
        if selected_countries == {"NONE"}: selected_countries.remove("NONE")
        selected_countries.add(iso_code)

    total_infections, total_deaths, total_vaccinations = get_total_stats()
    line_chart = get_line_chart()

    selection = [COUNTRIES[COUNTRIES["CCA3"] == cca3]["Country"].iloc[0]
                 for cca3 in selected_countries]

    markdown = f"""
    **Selected countries:** {selection}
    - Total infections: {total_infections}
    - Total deaths: {total_deaths}
    - Total vaccinations: {total_vaccinations}
    """

    return markdown, line_chart, get_map()

@callback(
    Output("map_content", "figure", allow_duplicate=True),
    Output("selected_date", "children"),
    Output("line_chart_content", "figure", allow_duplicate=True),
    Input("timeline_slider", "value"),
    prevent_initial_call=True
)
def on_year_change(date_index):
    print("Selected date: " + DATES[date_index])

    global date_selected
    date_selected = DATES[date_index]

    return get_map(), f"Date selected: {date_selected}", get_line_chart()

@callback(
    Output("map_content", "figure", allow_duplicate=True),
    Input("dropdown", "value"),
    prevent_initial_call=True
)
def on_dropdown_change(dropdown_value):
    global map_type, selected_countries
    map_type = dropdown_value

    return get_map()

# ----------------------------------- MAIN ------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
