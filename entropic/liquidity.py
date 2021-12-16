# %%
from typing import Tuple
import numpy as np
from scipy.optimize import curve_fit
import cvxpy as cp
import logging

_logger = logging.getLogger(__name__)


def exchange_function(
    x, liq1: float, liq2: float
) -> np.array:
    """
    Calculates the exchange function between two different assets:
    For x amount of asset1 return the amount of asset2 assumeing 
    a constant product exchange.
    Args:
        x: The amount of asset1 to be transferred
        liq1: The liquidity of the source asset
        liq2: The liquidity of the destination asset
    Returns:
        The x and y values of the exchange function
    """
    k = liq1 * liq2
    return liq2 - (k / (liq1 + x))

def _fit_func(x, a, b, c, d):
    """
    The functional form we are fitting to
    """
    return a * np.sqrt(b* x + c) + d

def _fit_func_dcp(x, a, b, c, d):
    """
    The functional form we are fitting to
    """
    return a * cp.sqrt(b* x + c) + d

def exchange_fit(x:np.array, liq1: float, liq2: float) -> np.array:
    """
    Since the exchange function is not DCP compliant we have to fit it to a DCP compliant function
    Args:
        liq1: The liquidity of the source asset
        liq2: The liquidity of the destination asset
    """
    popt = exchange_fit_params(x, liq1=liq1, liq2=liq2)
    return _fit_func(x, *popt)
    
def exchange_fit_params(x:np.array, liq1: float, liq2: float) -> np.array:
    """
    Get the parameters for the DCP compliant fit function
    """
    y0 = exchange_function(x, liq1=liq1, liq2=liq2)
    popt, _ = curve_fit(_fit_func, x, y0, method='trf')
    return popt

def convex_model(amt, A, B, C, D, S):
    """
    For a list of curves defined by:
        y_i = A_i * sqrt(B_i * x_i + C_i) + D_i
    Maximize:
        sum(y_i)
    Constraints:
        1. sum(x_i) < total
        2. y_i >= S_i * x_i
    Args:
        amt: total amount of liquidity to be exchanged
        A: set of A_i
        B: set of B_i
        C: set of C_i
        D: set of D_i
        S: set of S_i
    Returns:
        x_i: set of x_i
    """
    # initialize the variables
    x = cp.Variable(len(A))
    y = cp.multiply(A, cp.sqrt(cp.multiply(B, x) + C)) + D

    # Define the problem
    objective = cp.Maximize(cp.sum(y))
    constraints = [
        cp.sum(x) == amt,
        y >= cp.multiply(S, x)
    ]
    prob = cp.Problem(objective, constraints)
    prob.solve()

    if x.value is None:
        raise ValueError("No Feasible solution for convex model")
    return x.value.tolist()


# Old functions
# [TODO] Cleanup and remove


def linear_model(lines, slopes, amt):
    """
    For a set of lines defined by (m_i, b_i) and another set of slopes (s_i)
    Solve the following problem:
    For:
        y_i = m_i * x_i + b_i
    Maximize:
        sum(y_i)
    Constraints:
        1. sum(x_i) < total
        2. y_i >= s_i.T x_i
    Args:
        lines: set of (m_i, b_i)
        slopes: set of s_i
        amt: total amount of liquidity to be exchanged
    Returns:
        x_i: set of x_i

    Note:
        Without the additional slope constraint the problem is basically trivial.
        Since all of the assets will just go to the path with the highest slope
        This is essentially an artifact of the fact that the intercept is not zero.
        [TODO] I propose we set the intercept to zero for all linear fits for now.
        And generalize to non-linear functions later.
    """
    b = np.array([l_[0] for l_ in lines])
    m = np.array([l_[1] for l_ in lines])

    # initialize the variables
    x = cp.Variable(len(lines))
    y = cp.multiply(m, x) + b
    
    objective = cp.Maximize(cp.sum(y))

    constraints = [
        cp.sum(x) <= amt,
        y >= cp.multiply(slopes, x)
    ]

    prob = cp.Problem(objective, constraints)
    prob.solve()

    if x.value is not None:
        return x.value.tolist()
    else:
        _logger.warn("No Feasible solution for linear model")
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


def linear_model_old(lines, amt) -> list:
    """
    For a series of lines compute the following optimization problem:
    Maximize:
        The sum of output_var's
    Constained by:
        output_var_i - m_i * input_var_i==c_i
        output_var_i - slippage_i * input_var_i>=0
    sum of all input_var==amt
    Args:
        lines: list of dictionaries containing parameters
        (slope, intercept, slippage) values for all the k-shortest path
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
        equ_matrix[i][j + 1] = lines[i]["m"]
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
            pic_slope, pic_intercept, s_price = exchange_line(asset_a, asset_b, amt)
            slope.append(pic_slope)
            y_inter.append(pic_intercept)
            slippage_price.append(s_price)
        slope_dict[i] = slope
        inter_dict[i] = y_inter
        slippage_dict[i] = slippage_price

    return slope_dict, inter_dict, slippage_dict
