"""
Generate example data.
@author Ajmal | Advanced Blockchain AG
"""
import random
import numpy as np
from monty.serialization import dumpfn


# some settings for the graph size
NUM_SAMPLES = 6

# ==========================
max_num_cc_dex = 6  # Max Number of cross-chain DEXs
max_num_sc_dex = 10  # Max Number of source chain DEXs
max_num_dc_dex = 10  # Max Number of Destination chain DEXs
max_num_bridges = 6  # Number of Cross-chain Bridges
num_chains = 2
# num_network_tokens = 40
max_num_edges = 5
# sample edge data
maxspeed = 10
maxfee = 10
maxliquidity = 1e8
# ==========================

for samplenum in range(NUM_SAMPLES):
    print(f"  ...{NUM_SAMPLES - samplenum - 1}")

    nodes = [
        f"chain{i}" for i in range(num_chains)
    ]  # Source and destination chains for the Swap
    # print (f" Nodes... {nodes}")

    num_cc_dex = 0
    while num_cc_dex == 0:
        num_cc_dex = np.random.randint(max_num_cc_dex)
    # print (f" Cross_chain DEXs... {num_cc_dex}")
    # ---Generate Cross-chain DEXs---#
    cc_dexs = [f"cc_dex{i}" for i in range(num_cc_dex)]
    # print (f" Cross-chain DEX... {cc_dexs}")

    num_sc_dex = 0
    while num_sc_dex == 0:
        num_sc_dex = np.random.randint(max_num_sc_dex)
    # print (f" Source_chain DEXs... {num_sc_dex}")
    # ---Generate Source DEXs---#
    sc_dexs = [f"sc_dex{i}" for i in range(num_sc_dex)]
    sc_dex_in_degree = dict.fromkeys(
        sc_dexs, 0
    )  # initializing counter for the SC DEX incoming edges
    sc_dex_out_degree = dict.fromkeys(
        sc_dexs, 0
    )  # initializing counter for the SC DEX outgoing edges

    num_dc_dex = 0
    while num_dc_dex == 0:
        num_dc_dex = np.random.randint(max_num_dc_dex)
    # print (f" Destination_chain DEXs... {num_dc_dex}")

    # ---Generate Destination DEXs---#
    dc_dexs = [f"dc_dex{i}" for i in range(num_dc_dex)]
    dc_dex_in_degree = dict.fromkeys(
        dc_dexs, 0
    )  # initializing counter for the DC DEX incoming edges
    dc_dex_out_degree = dict.fromkeys(
        dc_dexs, 0
    )  # initializing counter for the DC DEX outgoing edges

    num_bridges = 0
    while num_bridges == 0:
        num_bridges = np.random.randint(max_num_bridges)
    # print (f" Number of bridges... {num_bridges}")

    # ---Generate cross-chain Bridges---#
    bridges = [f"bridge{i}" for i in range(num_bridges)]
    # print (f" Cross-Chain Bridges... {bridges}")

    # ----Generating the edges-----#

    # ---Generate edges for the cross-chain DEXs graph---#
    these_dexs = []
    for k in cc_dexs:
        thissource = nodes[0]
        thisdestination = nodes[1]
        thisspeed = np.random.randint(maxspeed)
        thisfee = np.random.randint(maxfee)
        thisexchangerate = random.uniform(3990, 4100)
        thisliquidity = np.random.randint(maxliquidity)
        line = (
            k,
            thissource,
            thisdestination,
            thisspeed,
            thisfee,
            thisliquidity,
            thisexchangerate,
        )
        these_dexs.append(line)

    for k in cc_dexs:
        num_edges = 0
        while num_edges == 0:
            num_edges = np.random.randint(max_num_edges)
        for i in range(0, num_edges):
            rdn = np.random.randint(20)  # Generate a Random num from 0 to 20
            if rdn < 10:  # edge between source chain DEX and destination chain
                thissource = random.choice(sc_dexs)
                sc_dex_out_degree[thissource] = sc_dex_out_degree[thissource] + 1
                thisdestination = nodes[1]
                thisspeed = np.random.randint(maxspeed)
                thisfee = np.random.randint(maxfee)
                thisexchangerate = random.uniform(3990, 4100)
                thisliquidity = np.random.randint(maxliquidity)
                line = (
                    k,
                    thissource,
                    thisdestination,
                    thisspeed,
                    thisfee,
                    thisliquidity,
                    thisexchangerate,
                )
                these_dexs.append(line)
            else:  # edge between Source chain and destination chain DEX
                thissource = nodes[0]
                thisdestination = random.choice(dc_dexs)
                dc_dex_in_degree[thisdestination] = (
                    dc_dex_in_degree[thisdestination] + 1
                )
                thisspeed = np.random.randint(maxspeed)
                thisfee = np.random.randint(maxfee)
                thisexchangerate = random.uniform(3990, 4100)
                thisliquidity = np.random.randint(maxliquidity)
                line = (
                    k,
                    thissource,
                    thisdestination,
                    thisspeed,
                    thisfee,
                    thisliquidity,
                    thisexchangerate,
                )
                these_dexs.append(line)

        # ---Generate liquidity, fee for the source-chain DEXs---#
    for k in sc_dexs:
        thissource = nodes[0]
        thisdestination = k
        sc_dex_in_degree[k] = sc_dex_in_degree[k] + 1
        # print(f" Source DEX {k}...In counter:{sc_dex_in_degree[k]}")
        thisspeed = np.random.randint(maxspeed)
        thisfee = np.random.randint(maxfee)
        thisexchangerate = random.uniform(0.98, 1.02)
        thisliquidity = np.random.randint(maxliquidity)
        line = (
            k,
            thissource,
            thisdestination,
            thisspeed,
            thisfee,
            thisliquidity,
            thisexchangerate,
        )
        these_dexs.append(line)

        # ---Generate liquidity, fee for the destination-chain DEXs---#
    for k in dc_dexs:
        thissource = k
        dc_dex_out_degree[k] = dc_dex_out_degree[k] + 1
        thisdestination = nodes[1]
        thisspeed = np.random.randint(maxspeed)
        thisfee = np.random.randint(maxfee)
        thisexchangerate = random.uniform(0.98, 1.02)
        thisliquidity = np.random.randint(maxliquidity)
        line = (
            k,
            thissource,
            thisdestination,
            thisspeed,
            thisfee,
            thisliquidity,
            thisexchangerate,
        )
        these_dexs.append(line)

        # ---Bridges---#

    for k in bridges:
        num_edges = 0
        while num_edges == 0:
            num_edges = int(np.mean([num_sc_dex, num_dc_dex]))
        # print(f" {k} edges: {num_edges}")
        for i in range(0, num_edges):
            rdn = np.random.randint(15)
            if rdn < 5:  # edge between source chain DEX and destination chain DEX
                thissource = random.choice(sc_dexs)
                sc_dex_out_degree[thissource] = sc_dex_out_degree[thissource] + 1
                # print(f" Source DEX {thissource}...Out counter:{sc_dex_out_degree[thissource]}")
                thisdestination = random.choice(dc_dexs)
                dc_dex_in_degree[thisdestination] = (
                    dc_dex_in_degree[thisdestination] + 1
                )
                thisspeed = np.random.randint(maxspeed)
                thisfee = np.random.randint(maxfee)
                thisexchangerate = random.uniform(3990, 4100)
                thisliquidity = np.random.randint(maxliquidity)
                line = (
                    k,
                    thissource,
                    thisdestination,
                    thisspeed,
                    thisfee,
                    thisliquidity,
                    thisexchangerate,
                )
                these_dexs.append(line)
            elif 5 <= rdn < 10:  # edge between Source chain DEX and destination chain
                thissource = random.choice(sc_dexs)
                sc_dex_out_degree[thissource] = sc_dex_out_degree[thissource] + 1
                # print(f" Source DEX {thissource}...Out counter:{sc_dex_out_degree[thissource]}")
                thisdestination = nodes[1]
                thisspeed = np.random.randint(maxspeed)
                thisfee = np.random.randint(maxfee)
                thisexchangerate = random.uniform(3990, 4100)
                thisliquidity = np.random.randint(maxliquidity)
                line = (
                    k,
                    thissource,
                    thisdestination,
                    thisspeed,
                    thisfee,
                    thisliquidity,
                    thisexchangerate,
                )
                these_dexs.append(line)
            else:  # edge between Source chain and destination chain DEX
                thissource = nodes[0]
                thisdestination = random.choice(dc_dexs)
                dc_dex_in_degree[thisdestination] = (
                    dc_dex_in_degree[thisdestination] + 1
                )
                thisspeed = np.random.randint(maxspeed)
                thisfee = np.random.randint(maxfee)
                thisexchangerate = random.uniform(3990, 4100)
                thisliquidity = np.random.randint(maxliquidity)
                line = (
                    k,
                    thissource,
                    thisdestination,
                    thisspeed,
                    thisfee,
                    thisliquidity,
                    thisexchangerate,
                )
                these_dexs.append(line)

        # ----Check if any Source-DEX or Destination DEX has zero in or out edge---#

        for key, value in sc_dex_out_degree.items():
            if value == 0:
                rdn = np.random.randint(10)
                if (
                    rdn < 5
                ):  # edge between source chain DEX and Destination chain (via cross-chain DEX)
                    thissource = key
                    sc_dex_out_degree[key] = sc_dex_out_degree[key] + 1
                    # print(f" Source DEX {key}...Out counter:{sc_dex_out_degree[key]}")
                    thisdestination = nodes[1]
                    thisspeed = np.random.randint(maxspeed)
                    thisfee = np.random.randint(maxfee)
                    thisexchangerate = random.uniform(3990, 4100)
                    thisliquidity = np.random.randint(maxliquidity)
                    line = (
                        random.choice(cc_dexs),
                        thissource,
                        thisdestination,
                        thisspeed,
                        thisfee,
                        thisliquidity,
                        thisexchangerate,
                    )
                    these_dexs.append(line)
                else:  # edge between source chain DEX and Bridge
                    thissource = key
                    sc_dex_out_degree[key] = sc_dex_out_degree[key] + 1
                    # print(f" Source DEX {key}...Out counter:{sc_dex_out_degree[key]}")
                    thisdestination = nodes[1]
                    thisspeed = np.random.randint(maxspeed)
                    thisfee = np.random.randint(maxfee)
                    thisexchangerate = random.uniform(3990, 4100)
                    thisliquidity = np.random.randint(maxliquidity)
                    line = (
                        random.choice(bridges),
                        thissource,
                        thisdestination,
                        thisspeed,
                        thisfee,
                        thisliquidity,
                        thisexchangerate,
                    )
                    these_dexs.append(line)

        for key, value in dc_dex_in_degree.items():
            if value == 0:
                rdn = np.random.randint(10)
                if (
                    rdn < 5
                ):  # edge between source chain and destination chain DEX (via random crosschain DEX)
                    thissource = nodes[0]
                    thisdestination = key
                    dc_dex_in_degree[key] = dc_dex_in_degree[key] + 1
                    # print(f" Destination DEX {key}...in counter:{dc_dex_in_degree[key]}")
                    thisspeed = np.random.randint(maxspeed)
                    thisfee = np.random.randint(maxfee)
                    thisexchangerate = random.uniform(3990, 4100)
                    thisliquidity = np.random.randint(maxliquidity)
                    line = (
                        random.choice(cc_dexs),
                        thissource,
                        thisdestination,
                        thisspeed,
                        thisfee,
                        thisliquidity,
                        thisexchangerate,
                    )
                    these_dexs.append(line)
                else:  # edge between source chain DEX and Bridge
                    thissource = nodes[0]
                    thisdestination = key
                    dc_dex_in_degree[key] = dc_dex_in_degree[key] + 1
                    # print(f" Destination DEX {key}...In counter:{dc_dex_in_degree[key]}")
                    thisspeed = np.random.randint(maxspeed)
                    thisfee = np.random.randint(maxfee)
                    thisexchangerate = random.uniform(3990, 4100)
                    thisliquidity = np.random.randint(maxliquidity)
                    line = (
                        random.choice(bridges),
                        thissource,
                        thisdestination,
                        thisspeed,
                        thisfee,
                        thisliquidity,
                        thisexchangerate,
                    )
                    these_dexs.append(line)

    settings = {
        "chains": list(nodes),
        "crosschain_dexs": list(cc_dexs),
        "sourcechain_dexs": list(sc_dexs),
        "destinationchain_dexs": list(dc_dexs),
        "bridges": list(bridges),
    }
    data = {"settings": settings, "data": these_dexs}
    dumpfn(data, "../test_files/da_test_example_{samplenum}.json", indent=2)
