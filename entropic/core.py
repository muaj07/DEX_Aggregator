# %%
from itertools import islice
import logging
from typing import Callable
import networkx as nx
from monty.json import MSONable
from monty.serialization import loadfn
from dataclasses import dataclass

__author__ = "jmmshn" "Ajk009"

_logger = logging.getLogger(__name__)


@dataclass
class DEXA(MSONable):
    """
    DEX Aggregator Represented as a graph
    """

    graph: nx.Graph

    @classmethod
    def from_list(cls, edge_list, node_list) -> "DEXA":
        """
        Creates a graph from a list of dicts
        Args:
            edge_list: A list of dicts, each dict representing an edge
            node_list: A list of dicts, each dict representing a node
        Returns:
            A instance of DEXA
        """
        graph = nx.Graph()
        for edge_dict in edge_list:
            # make sure the original data is preserved
            edge_kwargs = edge_dict.copy()
            edge_kwargs.pop("u")
            edge_kwargs.pop("v")
            graph.add_edge(edge_dict["u"], edge_dict["v"], **edge_kwargs)

        for node_dict in node_list:
            graph.nodes[node_dict["name"]].update(node_dict)
        for u,v,d in graph.edges(data=True):
            d['source_liquidity'] = graph.nodes[u].get('liquidity', 0)
            d['target_liquidity'] = graph.nodes[v].get('liquidity', 0)
        return cls(graph)

    @classmethod
    def from_file(cls, filename, liq_frac=1):
        """
        Creates a graph from a file
        Args:
            filename: A filename
            liq_frac: The fraction of liquidity allowed to be moved through each edge
        Returns:
            A graph
        """
        full_data = loadfn(filename)
        return cls.from_list(full_data["edges"], full_data["nodes"])

    def assign_weight(self, weight_func: Callable):
        """
        Assigns a weight to each edge in the graph using the available fee and liquidity data
        Args:
            weight_func: A function that takes a fee and 1/liquidity and returns a weight
        """
        for _, _, d in self.graph.edges(data=True):
            d["weight"] = weight_func(d)

    def get_pathways(self, source, target, num_of_paths):
        """
        Find the list the shortest path between two nodes. If liquidity is exhausted then look
        for the next shortest path.
        Args:
            source: The source node
            target: The target node
            num_of_paths: Total number of paths to report
        Returns:
            A list of nodes representing the shortest path
        """

        def k_shortest_paths(G, source, target, k, weight=None):
            return list(
                islice(nx.shortest_simple_paths(G, source, target, weight=weight), k)
            )

        return k_shortest_paths(self.graph, source, target, num_of_paths)
