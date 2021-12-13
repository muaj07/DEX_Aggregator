# %%
from pathlib import Path
import pytest
from entropic.core import DEXA

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"


@pytest.fixture
def files():
    """
    Returns a list of all test files in the test_files directory.
    """
    return {
        "nodes_edges": TEST_FILES_DIR / "nodes_edges.json",
    }


@pytest.fixture
def dexa(files):
    """
    Returns a DEXA object.
    """
    dexa = DEXA.from_file(files["nodes_edges"])
    assert set(dexa.graph.nodes.keys()) == {
        "Ethereum:DAI",
        "Ethereum:ETH",
        "Ethereum:MATIC",
        "Ethereum:SUSHI",
        "Ethereum:USDC",
        "Ethereum:USDT",
        "Polygon:AAVE",
        "Polygon:ADDY",
        "Polygon:ANY",
        "Polygon:BIFI",
        "Polygon:ETH",
        "Polygon:MATIC",
    }
    return dexa


def test_paths(dexa):
    """
    Test that finding the paths work correctly.
    """
    paths = dexa.get_pathways("Ethereum:SUSHI", "Polygon:BIFI", 5)
    assert len(paths) == 5
    for ip in paths:
        assert ip[0] == "Ethereum:SUSHI"
        assert ip[-1] == "Polygon:BIFI"
