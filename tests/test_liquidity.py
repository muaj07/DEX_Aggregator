# %%
from pathlib import Path
import pytest
import random
import cvxpy as cp
import numpy as np
from monty.serialization import loadfn
from entropic.liquidity import price_impact_curve

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"


@pytest.fixture
def path_data():
    return loadfn(TEST_FILES_DIR / "paths.json")


@pytest.fixture
def model_data():
    return loadfn(TEST_FILES_DIR / "linear_model.json")


def test_price_impact_curve(path_data):
    """
    Test the price impact curve function.
    All return values should be positive.
    """
    for ip in path_data:
        for edge in ip:
            asset_a = (0.5 * edge["liquidity"]) / edge["rate"]
            asset_b = 0.5 * edge["liquidity"]
            slope, intercept, price = price_impact_curve(asset_a, asset_b, 100)
            assert slope > 0
            assert intercept > 0
            assert price > 0


def test_liquidity_per_path(path_data, amt=100):
    """
    Test the estimated linear function for available liquidity on all paths
    All return values should be positive

    """
    for ip in path_data:
        for edge in ip:
            asset_a = (0.5 * edge["liquidity"]) / edge["rate"]
            asset_b = 0.5 * edge["liquidity"]
            slope, intercept, price = price_impact_curve(asset_a, asset_b, amt)
            assert slope > 0
            assert intercept > 0
            assert price > 0


def test_linear_model(model_data, amt=100):

    """
    Test the linear optimizatiom model for the order split of asset across given k-shortest paths
    The return value for x variables should not be none

    """
    equ_matrix = np.zeros((len(model_data), len(model_data) * 2))
    inequ_matrix = np.zeros((len(model_data), len(model_data) * 2))
    y_inter = np.array([sub["c"] for sub in model_data])
    # Define all the variables as x for the model
    all_var = cp.Variable(len(model_data) * 2, name="x")
    output_var = np.array([1 if i % 2 == 0 else 0 for i in range(len(model_data) * 2)])
    input_var = np.array([1 if i % 2 == 1 else 0 for i in range(len(model_data) * 2)])
    # Define the objective function for the model
    objective = cp.Maximize(output_var.T @ all_var)
    j = 0
    # setting the matrixs for constraints with equality and inequality
    for i in range(len(model_data)):
        equ_matrix[i][j] = 1
        equ_matrix[i][j + 1] = -model_data[i]["m"]
        inequ_matrix[i][j] = 1
        inequ_matrix[i][j + 1] = -model_data[i]["s"]
        j += 2
    # Define the constraint for the model
    constraints = [
        equ_matrix @ all_var == y_inter,
        inequ_matrix @ all_var >= np.array(np.zeros(len(model_data))),
        input_var.T @ all_var == amt,
        all_var >= 0,
    ]
    problem = cp.Problem(objective, constraints)
    problem.solve()
    assert all_var is not None
    assert sum((all_var.value).flatten("F")[1::2].tolist()) <= amt


def test_process_model_result(path_data):
    """
    Test the post-process function
    """
    # Values for asset-a split across
    actual_var = random.sample(range(10, 30), len(path_data))
    max_x_value = max(actual_var)
    max_x_index = actual_var.index(max_x_value)
    for i, ip in enumerate(actual_var):
        if ip < (max_x_value * 0.01):
            actual_var[max_x_index] = actual_var[max_x_index] + actual_var[i]
            actual_var[i] = 0
        # initialize dict for paths as keys and asset-B amount as values
        asset_amount = {}
        # estimating the amount of asset-B using the k-shortest paths and the split values
        for i, ip in enumerate(path_data):
            if actual_var[i] != 0:
                asset_amount[i] = actual_var[i]
                for edge in ip:
                    asset_a = (0.5 * edge["liquidity"]) / edge["rate"]
                    asset_b = 0.5 * edge["liquidity"]
                    k = asset_a * asset_b
                    asset_amount[i] = asset_b - (k / (asset_a + asset_amount[i]))
                    assert asset_amount[i] >= 0
