# %%
from pathlib import Path
import numpy as np
import pytest
import random
from monty.serialization import loadfn
from entropic.liquidity import convex_model, exchange_fit_params, exchange_function, linear_model

TEST_FILES_DIR = Path(__file__).parent.parent / "test_files"


@pytest.fixture
def path_data():
    return loadfn(TEST_FILES_DIR / "paths.json")


@pytest.fixture
def model_data():
    return loadfn(TEST_FILES_DIR / "linear_model.json")


def test_exchange_curve():
    """
    Test the exchange curve function.
    the path is given by a list of nodes with some finite liquidity
    """
    hop = {"source_liquidity": 10, "target_liquidity": 10}
    x = np.linspace(0, 10, 100)
    y = exchange_function(x, hop["source_liquidity"], hop["target_liquidity"])
    # check that the exchange function is monotonic
    assert np.all(np.diff(y) >= 0)
    # check that the exchange function is convex
    assert np.all(np.diff(y, 2) <= 0)


def test_convex_model():
    """
    What ever the model is, if we feed it two identical curves it should split the order evenly
    """
    x_grid = np.linspace(0, 100, 100)
    opt1 = exchange_fit_params(x_grid, liq1=100, liq2=100)
    opt2 = exchange_fit_params(x_grid, liq1=100, liq2=100)
    A, B, C, D = np.vstack([opt1, opt2]).T
    p1, p2 = convex_model(100, A, B, C, D, [0,0])
    assert pytest.approx(p1, 0.01) == pytest.approx(p2, 0.01)
    