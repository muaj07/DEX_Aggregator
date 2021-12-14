# %%
# import json
# from json2html import json2html
import dash
from dash import html
from dash.dependencies import Input, Output
import dash_cytoscape as cyto
from pathlib import Path
import dash_reusable_components as drc
import networkx as nx
from utils import get_graph_data

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"
file = TEST_FILES_DIR / "da_test_example_4.json"
plot_data, G = get_graph_data(file)
nodes_selection = [
    {"label": str(node), "value": str(node)}
    for node in G.nodes
    if str(node)[:5] != "chain"
]

# %%
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server

app.layout = html.Div(
    children=[
        # .container class is fixed, .container.scalable is scalable
        html.Div(
            className="banner",
            children=[
                # Change App Name here
                html.Div(
                    className="container scalable",
                    children=[
                        # Change App Name here
                        html.H2(
                            id="banner-title",
                            children=[
                                html.A(
                                    "Entropic Cross-Layer Decentralized Exchange Aggregator",
                                    style={
                                        "text-decoration": "none",
                                        "color": "inherit",
                                    },
                                )
                            ],
                        ),
                    ],
                )
            ],
        ),
        html.Div(
            id="body",
            className="container scalable",
            children=[
                html.Div(
                    id="app-container",
                    children=[
                        html.Div(
                            id="left-column",
                            children=[
                                drc.Card(
                                    id="select-node-card",
                                    children=[
                                        drc.NamedDropdown(
                                            id="from_node",
                                            name="From Node",
                                            options=nodes_selection,
                                            value=nodes_selection[0]["value"],
                                        ),
                                        drc.NamedDropdown(
                                            id="to_node",
                                            name="To Node",
                                            options=nodes_selection,
                                            value=nodes_selection[1]["value"],
                                        ),
                                    ],
                                ),
                            ],
                            style={"padding": 200, "flex": 1},
                        ),
                    ],
                ),
                cyto.Cytoscape(
                    id="cytoscape-graph",
                    layout={"name": "preset"},
                    style={
                        "width": "80%",
                        "height": "900px",
                        "background-color": "#e3e3e3",
                    },
                    elements=plot_data["nodes"] + plot_data["edges"],
                ),
                html.Div(
                    id="slections",
                ),
            ],
        ),
    ]
)


@app.callback(
    Output("slections", "children"),
    [Input("from_node", "value"), Input("to_node", "value")],
)
def update_1(from_node, to_node):
    return from_node, to_node


@app.callback(
    Output("cytoscape-graph", "stylesheet"),
    [Input("from_node", "value"), Input("to_node", "value")],
)
def update_update_cyto(from_node, to_node):
    style_sheet = [
        {"selector": "node", "style": {"content": "data(label)"}},
        {
            "selector": f"[label = '{from_node}']",
            "style": {
                "background-color": "#FF4136",
            },
        },
        {
            "selector": f"[label = '{to_node}']",
            "style": {
                "background-color": "#FF4136",
            },
        },
    ]
    uG = G.to_undirected()
    paths = nx.shortest_path(uG, from_node, to_node)
    hops = list(zip(paths[:-1], paths[1:]))
    for ihop in hops:
        style_sheet.append(
            {
                "selector": f"#{ihop[1]}-{ihop[0]}",
                "style": {
                    "line-color": "#FF4136",
                },
            }
        )
        style_sheet.append(
            {
                "selector": f"#{ihop[0]}-{ihop[1]}",
                "style": {
                    "line-color": "#FF4136",
                },
            }
        )
    return style_sheet


if __name__ == "__main__":
    app.run_server(debug=True)
