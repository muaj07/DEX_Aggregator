from pprint import pprint
import numpy as np
from networkx.drawing.layout import spring_layout
from networkx.readwrite import json_graph
from entropic.liquidity import price_impact_curve, price_impact_line
from entropic.core import DEXA
import pandas as pd
import plotly.express as px


def _modify_nodes(data, positions):
    """Add label and position to each node"""
    for node in data["nodes"]:
        node["data"]["label"] = node["data"]["id"]
        x, y = positions[node["data"]["id"]]
        node["position"] = {"x": x, "y": y}
        node["classes"] = f'dex_{node["data"]["name"].split(":")[0]}'

    for edge in data["edges"]:
        edge["data"]["id"] = edge["data"]["source"] + "-" + edge["data"]["target"]
        if edge["data"].get("isBridge", False):
            edge["classes"] = "bridge"


def get_graph_data(file, spring_layout_kwargs=None):
    """
    Read a json file to construct the DEXA and return the basic plotting
    information for the graph along with the graph itself.
    Additional information can be added to the final graph by modifying modifying the graph plotting dictionary.

    Args:
        file (str): The path to the json file.
        spring_layout_kwargs (dict): The kwargs to pass to the spring layout.
    Returns:
        plot_data: The plotting information for the graph.
        graph: the nx graph object
    """
    spring_layout_kwargs = spring_layout_kwargs or {}
    router = DEXA.from_file(file)
    G = router.graph.copy()
    rm_bunch = [[u, v] for u, v in G.edges() if u.split(":")[0] != v.split(":")[0]]
    G.remove_edges_from(rm_bunch)
    positions = spring_layout(
        G, k=140, iterations=25, weight="weight", scale=10, **spring_layout_kwargs
    )

    plot_data = json_graph.cytoscape_data(router.graph)["elements"]
    _modify_nodes(plot_data, positions=positions)
    return plot_data, router.graph


def get_price_impact_curve(edge_data, amt):
    """
    Get the plotly figure price impact curve for a given edge and amount
    Args:
        edge_data (dict): edge data
        amt (float): amount
    Returns:
        plotly figure
    """
    pprint(edge_data)
    # Since cytroscape does not support default selection, we need placeholder data before a click is made
    if edge_data:
        liq_1 = edge_data['source_liquidity']
        liq_2 = edge_data["target_liquidity"]
        xx, yy = price_impact_curve(
            liq_1, liq_2, amt=amt
        )
        slope, intercept, price = price_impact_line(
            liq_1, liq_2, amt=amt, slippage=0.95
        )
        yy_fit = slope * xx + intercept
    else:
        xx = np.linspace(0, amt, 100)
        yy = xx
        yy_fit = yy
    
    df = pd.DataFrame({"Amount": xx, "Price Impact": yy, "Fit": yy_fit})
    fig = px.line(df, x="Amount", y=["Price Impact", "Fit"], template="plotly_dark")
    fig.update_layout(
        plot_bgcolor="#282b38",
        paper_bgcolor="#282b38",
        font=dict(size=20),
        legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99),
    )
    return fig
