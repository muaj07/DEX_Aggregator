# %%
from pathlib import Path
import pytest
import random
from monty.serialization import loadfn
from entropic.liquidity import price_impact_curve, linear_model

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"


@pytest.fixture
def path_data():
    return loadfn(TEST_FILES_DIR / "paths.json")


@pytest.fixture
def model_data():
    return loadfn(TEST_FILES_DIR / "linear_model.json")


def test_price_impact_curve():
    """
    Test the price impact curve function.
    the path is given by a list of nodes with some finite liquidity
    """
    hop = {"source_liquidity": 1, "target_liquidity": 1}
    xx, yy = price_impact_curve(hop["source_liquidity"], hop["target_liquidity"], 1)
    assert max(xx) <= 1


def test_linear_model():
    """
    Test the linear optimizatiom model for the order split of asset across given k-shortest paths
    The return value for x variables should not be none
    """
    lines = [[10.5, 3.9], [9.84, 4.0]]
    slopes = [3.9, 4.09]
    res = linear_model(lines, slopes, 500)
    assert res[0] == pytest.approx(390.66667)
    assert res[1] == pytest.approx(109.33332)


# def test_process_model_result(path_data):
#     """
#     Test the post-process function
#     """
#     # Values for asset-a split across
#     actual_var = random.sample(range(10, 30), len(path_data))
#     max_x_value = max(actual_var)
#     max_x_index = actual_var.index(max_x_value)
#     for i, ip in enumerate(actual_var):
#         if ip < (max_x_value * 0.01):
#             actual_var[max_x_index] = actual_var[max_x_index] + actual_var[i]
#             actual_var[i] = 0
#         # initialize dict for paths as keys and asset-B amount as values
#         asset_amount = {}
#         # estimating the amount of asset-B using the k-shortest paths and the split values
#         for i, ip in enumerate(path_data):
#             if actual_var[i] != 0:
#                 asset_amount[i] = actual_var[i]
#                 for edge in ip:
#                     asset_a = (0.5 * edge["liquidity"]) / edge["rate"]
#                     asset_b = 0.5 * edge["liquidity"]
#                     k = asset_a * asset_b
#                     asset_amount[i] = asset_b - (k / (asset_a + asset_amount[i]))
#                     assert asset_amount[i] >= 0


# %%
