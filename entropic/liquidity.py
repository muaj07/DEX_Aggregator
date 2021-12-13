# %%
from typing import Tuple
import numpy as np
import cvxpy as cp
import logging

_logger = logging.getLogger(__name__)


def price_impact_curve(x, y, amt, slippage=0.95) -> Tuple[float, float, float]:
    """
    Calculates the price impact curve between two different assets by
    fitting a linear function to the data between [0, amt]
    Args:
        x: The liquidity of the source asset
        y: The liquidity of the destination asset
        amt: The amount of liquidity to be transferred
        slippage: The slippage factor
    Returns:
        A tuple of the price impact info:
        (slope, intercept, price_estimate)
    """
    k = x * y
    a = np.linspace(0, amt, 100)
    b = y - (k / (x + a))
    slope, intercept = np.polyfit(a, b, 1)
    price_estimate = (y - (k / (x + 1))) * slippage
    return slope, intercept, price_estimate


def liquidity_per_path(paths, amt) -> Tuple[dict, dict, dict]:
    """
    Calculates the linear function (slope, intercept) for all the edges
    of k-shortest paths using the available liquidity at the path edges
    and the given exchange rate
    Args:
        paths: Set of k-shortest path between source and destination chains
        amt: The amount of liquidity to be exchanged/swapped
    Returns:
        A tuple of the dictionaries for path liquidity info:
        (slope_dict, intercept_dict, price_estimate_dict)
    """
    slope_dict = {}
    inter_dict = {}
    slippage_dict = {}
    i = 0
    for i, ip in enumerate(paths):
        slope = []
        y_inter = []
        slippage_price = []
        for edge in ip:
            asset_a = (0.5 * edge["liquidity"]) / edge["rate"]
            asset_b = 0.5 * edge["liquidity"]
            print(edge["bridge"])
            pic_slope, pic_intercept, s_price = price_impact_curve(
                asset_a, asset_b, amt
            )
            slope.append(pic_slope)
            y_inter.append(pic_intercept)
            slippage_price.append(s_price)
        slope_dict[i] = slope
        inter_dict[i] = y_inter
        slippage_dict[i] = slippage_price

    return slope_dict, inter_dict, slippage_dict


def linear_model(lines, amt) -> list:
    """
    For a series of lines compute the following optimization problem:
    Maximize: the sum of output_var's
    Constained by:
    output_var_i - m_i input_var_i==c_i
    output_var_i - slippage_i input_var_i>=0
    sum of all input_var==amt
    Args:
    lines: list of dictionaries containing parameters (slope, intercept, slippage) values
    for all the k-shortest path
    Return:
    list of variables values
    """
    equ_matrix = np.zeros((len(lines), len(lines) * 2))
    inequ_matrix = np.zeros((len(lines), len(lines) * 2))
    y_inter = np.array([sub["c"] for sub in lines])
    # Define all the variables as x for the model
    all_var = cp.Variable(len(lines) * 2, name="x")
    output_var = np.array([1 if i % 2 == 0 else 0 for i in range(len(lines) * 2)])
    input_var = np.array([1 if i % 2 == 1 else 0 for i in range(len(lines) * 2)])
    # Define the objective function for the model
    objective = cp.Maximize(output_var.T @ all_var)
    j = 0
    # setting the matrixs for constraints with equality and inequality
    for i in range(len(lines)):
        equ_matrix[i][j] = 1
        equ_matrix[i][j + 1] = -lines[i]["m"]
        inequ_matrix[i][j] = 1
        inequ_matrix[i][j + 1] = -lines[i]["s"]
        j += 2
    # Define the constraint for the model
    constraints = [
        equ_matrix @ all_var == y_inter,
        inequ_matrix @ all_var >= np.array(np.zeros(len(lines))),
        input_var.T @ all_var == amt,
        all_var >= 0,
    ]
    problem = cp.Problem(objective, constraints)
    # Solve the model
    problem.solve()
    # if feasible solution exist the return the values of input variables
    # ie., the split value for asset-a across k-shortest path
    # from these split values we will calculate the estimated amount of asset-b using the
    # available liquidity
    if all_var.value is not None:
        return (all_var.value).flatten("F")[1::2].tolist()
    else:
        _logger.info("No Feasible solution")
        _logger.info(
            "Either increase the slippage value or number of paths to obtain a feasible solution"
        )
        print("No Feasible solution")
        return []


def process_model_result(paths, actual_var):
    """
    Post_process the linear model solution by using the asset-a split values
    across k-shortest paths and the available liquidity on these paths to
    estimate the amount of received asset-b
    Args:
        paths: set of the computed k-shortest path
        actual_var: list of split values for asset-a across k-shortest paths
        Returns:
        asset_amount: list of estimated asset-b amount to be received after swap of asset-a
        sum(asset_amount): total estimated amount of asset-b after swap of asset-a
    """
    # we need to do some clearing by removing x's with low values making them zero
    # and adding those low values to x that has maximum value
    max_x_value = max(actual_var)
    max_x_index = actual_var.index(max_x_value)
    for i, ip in enumerate(actual_var):
        if ip < (max_x_value * 0.01):
            actual_var[max_x_index] = actual_var[max_x_index] + actual_var[i]
            actual_var[i] = 0
        # initialize dict for paths as keys and asset-B amount as values
        asset_amount = {}
        # estimating the amount of asset-B using the k-shortest paths and the split values
        for i, ip in enumerate(paths):
            if actual_var[i] != 0:
                asset_amount[i] = actual_var[i]
                for edge in ip:
                    asset_a = (0.5 * edge["liquidity"]) / edge["rate"]
                    asset_b = 0.5 * edge["liquidity"]
                    k = asset_a * asset_b
                    asset_amount[i] = asset_b - (k / (asset_a + asset_amount[i]))
    return asset_amount, sum(asset_amount.values())


def prior_to_model(slope_dict, intercept_dict, slippage_dict):
    """
    create a list of dictionaries where the keys will be the slope, y_intercept, and
    tolerable price slippage for all the k-shortest paths
    Args:
        slope_dict: slope values for the estimated linear functions for all paths
        intercept_dict: intercept values for the estimated linear functions for all paths
        slippage_dict: tolerable price slippage values for swap over k-shortest paths
        Returns:
        A list of dictionaries:
        [{"m":value, "c":value,. "s":value}.....{"m":value, "c":value,. "s":value}]
    """
    lines_list = []
    j = 0
    for i in range(len(slope_dict)):
        if len(slope_dict[i]) == 1:
            lines_list.append(
                {
                    "m": np.prod(slope_dict[i]),
                    "c": intercept_dict[i][0],
                    "s": slippage_dict[i][0],
                }
            )
        elif len(slope_dict[i]) == 2:
            lines_list.append(
                {
                    "m": np.prod(slope_dict[i]),
                    "c": (slope_dict[i][1] * intercept_dict[i][0])
                    + intercept_dict[i][1],
                    "s": max(slippage_dict[i]),
                }
            )
        else:
            lines_list.append(
                {
                    "m": np.prod(slope_dict[i]),
                    "c": (slope_dict[i][1] * slope_dict[i][2] * intercept_dict[i][0])
                    + (slope_dict[i][2] * intercept_dict[i][1])
                    + intercept_dict[i][2],
                    "s": max(slippage_dict[i]),
                }
            )
            j = j + 2
    return lines_list
