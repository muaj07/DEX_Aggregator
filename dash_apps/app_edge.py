# %%
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_cytoscape as cyto
from pathlib import Path
import dash_reusable_components as drc
from utils import get_graph_data, get_price_impact_curve

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"
file = TEST_FILES_DIR / "nodes_edges.json"
spring_layout_kwargs = dict(
    pos={"Polygon:ETH": (300, 0), "Ethereum:ETH": (0, 0)},
    fixed=["Ethereum:ETH", "Polygon:ETH"],
)
plot_data, _ = get_graph_data(file, spring_layout_kwargs)
IMAGE_DIR = Path(__file__).parent / "assets"
for node in plot_data["nodes"]:
    cc_name = node["data"]["name"].split(":")[-1]
    img_file = f"https://raw.githubusercontent.com/jmmshn/vacation_routing/main/assets/{cc_name}.png"
    node["data"]["image"] = str(img_file)
style_sheet = [
    {
        "selector": "node",
        "style": {
            "content": "data(name)",
            "background-fit": "none",
            "background-width": ["24px", "20px", "20px"],
            "background-height": ["24px", "20px", "20px"],
            "background-image": "data(image)",
        },
    },
    {
        "selector": ".bridge",
        "style": {
            "line-color": "#27183B",
        },
    },
    {
        "selector": ".dex_Polygon",
        "style": {
            "background-color": "#35EBEB",
        },
    },
    {
        "selector": ".dex_Ethereum",
        "style": {
            "background-color": "#FF4136",
        },
    },
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
                                    id="sliders",
                                    children=[
                                        drc.NamedSlider(
                                            id="transfer-amount",
                                            name="Transfer Amount",
                                            min=0,
                                            max=100000,
                                            value=6000,
                                            step=1,
                                            tooltip={
                                                "placement": "bottom",
                                                "always_visible": True,
                                            },
                                        ),
                                    ],
                                ),
                                drc.Card(id="card-1", children=html.A("Edge Data")),
                                drc.Card(id="card-2", children=html.A(id="edge-info")),
                                drc.Card(
                                    id="card-3",
                                    children=dcc.Loading(
                                        className="graph-wrapper",
                                        children=dcc.Graph(
                                            id="price-impact-graph",
                                        ),
                                    ),
                                ),
                            ],
                        ),
                        html.Div(
                            id="div-graphs",
                            children=[
                                cyto.Cytoscape(
                                    id="cytoscape-graph",
                                    layout={"name": "preset"},
                                    style={
                                        "width": "80%",
                                        "height": "900px",
                                        "background-color": "#e3e3e3",
                                    },
                                    stylesheet=style_sheet,
                                    elements=plot_data["nodes"] + plot_data["edges"],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ]
)


@app.callback(Output("edge-info", "children"), Input("cytoscape-graph", "tapEdgeData"))
def displayTapNodeData(data):
    if data:
        show_keys = ["fee", "source_liquidity", "target_liquidity"]
        return html.Table(
            [html.Tr([html.Th(key), html.Td(data[key])]) for key in show_keys]
        )


@app.callback(
    Output("price-impact-graph", "figure"),
    [Input("cytoscape-graph", "tapEdgeData"), Input("transfer-amount", "value")],
)
def update_price_impact_graph(edge_data, amt):
    return get_price_impact_curve(edge_data, amt)


if __name__ == "__main__":
    app.run_server(debug=True)
