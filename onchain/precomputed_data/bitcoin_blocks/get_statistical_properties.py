import json
import os
import re
import requests
from collections import Counter
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from collections import defaultdict
import statistics
import pandas as pd
import numpy as np
from itertools import combinations
from scipy.stats import percentileofscore


# constants
DATASET_PATH = '../data/'
TRANSACTIONS_FILE_PATH = 'precomputed_data/transactions.json'
API_URL = "https://blockstream.info/api/"
OPENED_AND_CLOSED_CHANNELS_OVER_TIME_PATH = "precomputed_data/opened_and_closed_channels_over_time.json"
OPENED_AND_CLOSED_NODES_OVER_TIME_PATH = "precomputed_data/opened_and_closed_nodes_over_time.json"
FIXED_OPENED_AND_CLOSED_CHANNELS_OVER_TIME_PATH = "precomputed_data/fixed_opened_and_closed_channels_over_time.json"
FIXED_OPENED_AND_CLOSED_NODES_OVER_TIME_PATH = "precomputed_data/fixed_opened_and_closed_nodes_over_time.json"
CHANNEL_POINTS_PATH = "precomputed_data/channel_points.json"
BITCOIN_DATASET_PATH = "../elenvisualizations/website_data/aux_data/price_market_per_day.csv"


def get_transaction_by_id(tx_id):
    """
    Fetch the details of a Bitcoin transaction given its id.
    """
    url = f'{API_URL}tx/{tx_id}'
    try:
        response = requests.get(url, timeout=10) 
        response.raise_for_status() # raise an exception if the request fails
        print(f"Response from {url}: {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transaction {tx_id}: {e}")
        return None


# get the channel points of the LN channels
# a channel point is a on-chain reference of a lightning channel that
# is a on-chain transaction output that opens the channel (<tx id>:<output index>)
def get_channel_points(snapshots_name):
    """
    Extract the channel points (on-chain references) from the snapshots of the Lightning Network
    """
    channel_points_set = set()
    for snapshot_name in snapshots_name:  
        print("Parsing LN snapshot: " + snapshot_name)
        with open(DATASET_PATH + snapshot_name, 'r') as file:
            data = json.load(file)
            print("timestamp----")
            print(data['timestamp'])
            print("timestamp----")

        for channel in data['edges']:
            channel_points_set.add(channel['chan_point'])
    return list(channel_points_set)

def print_percentage_distribution(distribution, total, first_n):
    sorted_data = sorted(distribution, key=lambda x: x[1], reverse=True)
    for i in range(first_n):
        percentage = (sorted_data[i][1] / total) * 100  # Calculating percentage
        print(f"Key: {sorted_data[i][0]}, Frequency: {percentage:.3f} %")

def get_percentage_of_firsts_n_most_frequent_keys(distribution, total, n):
    sorted_data = sorted(distribution, key=lambda x: x[1], reverse=True)
    # Calculate the percentage
    res = 0
    for i in range(n):
        res += sorted_data[i][1] / total
    return res
        

# create a file that contains the on chain transactions related to the channel points
def create_on_chain_transactions_file(channel_points, output_file):
    
    """
    Save all LN channel-related on-chain transactions to a file.
    """
    transactions = []
    total_points = len(channel_points)
    missing_count = 0

    for idx, chan_point in enumerate(channel_points, start=1):
        tx_id, output_index = chan_point.split(':')
        print(f"Fetching transaction {idx}/{total_points}: tx_id={tx_id} (output index={output_index})")
        
        transaction = get_transaction_by_id(tx_id)
        if transaction:
            transactions.append({
                "chan_point": chan_point,
                "transaction": transaction
            })
        else:
            print(f"Transaction missing for chan_point: {chan_point}")
            missing_count += 1
        
        # print(f"Progress: {idx}/{total_points} completed. Missing transactions so far: {missing_count}")
        print(f"Progress: {idx}/{total_points} completed.")
    
    with open(output_file, 'w') as file:
        json.dump(transactions, file, indent=4)
    
    print(f"Processing complete. Saved {len(transactions)} transactions to {output_file}.")
    # print(f"Total missing transactions: {missing_count}")


# get the on-chain transactions list 
def get_on_chain_transactions_list(on_chain_transactions_file):
    """
    Load a previously saved list of LN on-chain transactions from a file.
    """
    with open(on_chain_transactions_file, 'r') as file:
        transactions = json.load(file)
    return transactions


# get output index distribution of channel points
def get_output_index_distribution(channel_points):
    """
    Compute the output index distribution of the channel points
    """
    outputs_index = [int(channel_point.split(':')[1]) for channel_point in channel_points]
    # Count occurrences of each index
    distribution = Counter(outputs_index)
    # Sort distribution by key and convert it into a list of tuples
    return sorted(distribution.items())

# Input number distribution of on chain LN channels
def get_input_number_distribution(on_chain_transactions):
    """
    Compute the distribution of the number of inputs in the LN on-chain transactions.
    """
    num_inputs = [len(tx["transaction"]["vin"]) for tx in on_chain_transactions]
    return Counter(num_inputs).most_common()
    
    

# Output number distribution (with percentages)
def get_output_number_distribution(on_chain_transactions):
    """
    Compute the distribution of the number of outputs in the LN on-chain transactions.
    """
    num_outputs = [len(tx["transaction"]["vout"]) for tx in on_chain_transactions]
    # return Counter(num_outputs).most_common()

    distribution = Counter(num_outputs)
    # Sort distribution by key and convert it into a list of tuples
    return sorted(distribution.items())
    

# get percentage of LN on chain transactions with a P2WSH output
def percentage_with_less_than_n_p2wsh_output(transactions, n):
    """
    Calculate the percentage of transactions with exactly one 'v0_p2wsh' output.
    """
    count = sum(
        1 for tx in transactions if sum(
            output["scriptpubkey_type"] == "v0_p2wsh" for output in tx["transaction"]["vout"]
        ) < n
    )
    return (count / len(transactions)) * 100



# Function to calculate the percentage of transactions with outputs < 420,000,000 satoshis
def percentage_with_outputs_below_threshold(transactions, threshold=420000000):
    """
    Calculate the percentage of transactions with at least one output below the given threshold.
    """
    count = sum(
        1 for tx in transactions if any(output["value"] < threshold and output["scriptpubkey_type"] == "v0_p2wsh"  for output in tx["transaction"]["vout"])
    )
    return (count / len(transactions)) * 100

# Function to calculate the percentage of transactions with at least one input of either P2WKH or P2SH
def percentage_with_p2wpkh_or_p2sh_inputs(transactions):
    """
    Calculate the percentage of LN on-chain transactions that have at least one input of type P2WKH or P2SH.
    """
    count = sum(
            1 for tx in transactions if any(output['prevout']["scriptpubkey_type"] == "v0_p2wpkh" or output['prevout']["scriptpubkey_type"] == "v1_p2tr"  for output in tx["transaction"]["vin"])
    )
    return (count / len(transactions)) * 100
 

def get_script_types(transactions):
    """
    Calculate the percentage of LN on-chain transactions that have at least one input of type P2WKH or P2SH.
    """
    script_types = set()
    for tx in transactions:
        for _input in tx['transaction']['vin']:
            script_types.add(_input['prevout']['scriptpubkey_type'])
    return script_types

    


def extract_date_from_filename(filename):
    """
    Extracts the date string (YYYY_MM_DD) from a filename formatted as 'prefix_YYYY_MM_DD.suffix'.

    Args:
        filename (str): The filename to process.

    Returns:
        str: The extracted date string in 'YYYY_MM_DD' format, or None if no match is found.
    """
    match = re.search(r'\d{4}_\d{2}_\d{2}', filename)
    return match.group(0) if match else None



def get_hours_distance(timestamp1, timestamp2):
    if not timestamp1 or not timestamp2:  # Check if either timestamp is an empty string
        return -1
    
    format_str = "%Y_%m_%d_%H_%M"  # Define the expected format
    dt1 = datetime.strptime(timestamp1, format_str)
    dt2 = datetime.strptime(timestamp2, format_str)
    res = abs((dt2 - dt1).total_seconds() / 60 / 60)  # Calculate absolute difference in hours
    print("xxxxxx")
    print("")
    print("timestamp1:"+ str(timestamp1))
    print("timestamp2:"+ str(timestamp2))
    print("res"+ str(res*60))

    return res



def get_opened_and_closed_channels_over_time(snapshots_name):
    """
    Extract the channel points (on-chain references) and the number of edges (channels)
    from the snapshots of the Lightning Network.
    """
    previous_channel_points = set()
    previous_timestamp = ""
    measurements = []
    for snapshot_name in snapshots_name:
        print(f"Parsing LN snapshot: {snapshot_name}")
        
        # Load the snapshot data
        with open(DATASET_PATH + snapshot_name, 'r') as file:
            data = json.load(file)
        
        # Extract current snapshot's channel points
        current_channel_points = {channel['chan_point'] for channel in data['edges']}
        
        # Calculate opened and closed channels
        opened_channels = current_channel_points - previous_channel_points
        closed_channels = previous_channel_points - current_channel_points
        # print(f"------------------closed channels at {snapshot_name} :")
        # print(closed_channels)
        # print("-------")


        # get the timestamp
        current_timestamp = data['timestamp']
        hours_distance = get_hours_distance(current_timestamp, previous_timestamp)

        # print("------")
        # print("Get hours distance:")
        # print(str(hours_distance))
        # print("from current_timestamp to previous_timestamp:")
        # print(str(current_timestamp) + "    " + str(previous_timestamp))


        aux = snapshot_name.split(".")[0]
        date_part = aux.split("_")[2:5] 
        timestamp = "-".join(date_part)
        
        # print("No opened channels:")
        # print(str(len(opened_channels)))
        # print("No closed channels:")
        # print(str(len(closed_channels)))
        # print("No opened channels with normalization:")
        # print(str(len(opened_channels)/hours_distance))
        # print("No closed channels with normalization:")
        # print(str(len(closed_channels)/hours_distance))

        # Record the results
        measurements.append({
            "timestamp": timestamp,
            "opened_channels": len(opened_channels)/ hours_distance,
            "closed_channels": len(closed_channels)/ hours_distance,
            "total_channels": len(data['edges'])  # Total number of edges in the snapshot
        })
        
        # Update the previous_channel_points for the next iteration
        previous_channel_points = current_channel_points
        previous_timestamp = current_timestamp



    return measurements


def get_opened_and_closed_nodes_over_time(snapshots_name):
    """
    Extract the channel points (on-chain references) and the number of edges (channels)
    from the snapshots of the Lightning Network.
    """
    previous_nodes = set()
    previous_timestamp = ""
    measurements = []
    for snapshot_name in snapshots_name:
        print(f"Parsing LN snapshot: {snapshot_name}")
        
        # Load the snapshot data
        with open(DATASET_PATH + snapshot_name, 'r') as file:
            data = json.load(file)

        current_timestamp = data['timestamp']
        hours_distance = get_hours_distance(current_timestamp, previous_timestamp)

        # print("------")
        # print("Get hours distance:")
        # print(str(hours_distance))
        # print("from current_timestamp to previous_timestamp:")
        # print(str(current_timestamp) + "    " + str(previous_timestamp))
        
        # Extract current snapshot's channel points
        current_nodes = {node['pub_key'] for node in data['nodes']}
        
        # Calculate opened and closed channels
        opened_nodes = current_nodes - previous_nodes
        closed_nodes = previous_nodes - current_nodes

        # get the timestamp
        aux = snapshot_name.split(".")[0]
        date_part = aux.split("_")[2:5] 
        timestamp = "-".join(date_part)

        
        
        # Record the results
        # print("No opened nodes:")
        # print(str(len(opened_nodes)))
        # print("No closed nodes:")
        # print(str(len(closed_nodes)))
        measurements.append({
            "timestamp": timestamp,
            "opened_nodes": len(opened_nodes)/hours_distance,
            "closed_nodes": len(closed_nodes)/hours_distance,
            "total_nodes": len(data['nodes'])  # Total number of edges in the snapshot
        })
        
        # Update the previous_channel_points for the next iteration
        previous_nodes = current_nodes
        previous_timestamp = current_timestamp

    return measurements

def is_hole(data, index):
    if index == 0:
        return False
    
    # Parse the current timestamp string to a datetime object
    current_sample_date = datetime.strptime(data[index]['timestamp'], '%Y-%m-%d')
    
    # Parse the previous timestamp string to a datetime object
    previous_sample_date = datetime.strptime(data[index-1]['timestamp'], '%Y-%m-%d')
    
    # Calculate the difference in days
    delta = current_sample_date - previous_sample_date
    return delta.days > 1

def fix_zero(data, index, timeseries_key):
    if len(data) < 1:
        print("Error: samples are less than 2")
        return 
    if index == len(data) - 1:
        data[index][timeseries_key] = data[index-1][timeseries_key]
    elif index == 0:
        data[index][timeseries_key] = data[index+1][timeseries_key]
    else:
        data[index][timeseries_key] = statistics.mean([data[index-1][timeseries_key], data[index+1][timeseries_key]])



def fix_hole(data, index, timeseries_key):
    # if it's the last sample just copy the values of the previous sample
    if index == len(data) - 1:
        data[index][timeseries_key] = data[index-1][timeseries_key]
    else:
        data[index][timeseries_key] = statistics.mean([data[index-1][timeseries_key], data[index+1][timeseries_key]])


def fix_timeseries(data, timeseries_key):
    for index, timeseries in enumerate(data):
        if is_hole(data, index):
            fix_hole(data, index, timeseries_key)
            continue
        if data[index][timeseries_key] == 0:
            fix_zero(data, index, timeseries_key)
    with open(FIXED_OPENED_AND_CLOSED_CHANNELS_OVER_TIME_PATH, 'w') as file:
        json.dump(data, file, indent=4)
    return data

def integrate_with_bitcoin_value(data, path):
    # Load the Bitcoin dataset
    bitcoin_dataset = pd.read_csv(path)

    # Convert the 'price' column in the dataset to datetime.date format
    bitcoin_dataset['snapped_at'] = pd.to_datetime(bitcoin_dataset['snapped_at'], errors='coerce').dt.date
    # Iterate over the timeseries data
    for index, timeseries in enumerate(data):
        # Extract and normalize the timestamp in the current timeseries to datetime.date
        date = datetime.strptime(timeseries['timestamp'], '%Y-%m-%d').date()
        # Find the matching row in the Bitcoin dataset
        matching_row = bitcoin_dataset[bitcoin_dataset['snapped_at'] == date]
        # If a matching row exists, update the timeseries data
        if not matching_row.empty:
            data[index]['bitcoin_value'] = matching_row.iloc[0]['price']  # Adjust 'bitcoin_value' to the actual column name in your dataset
        else:
            data[index]['bitcoin_value'] = None  # Handle cases where no match is found
    return data

def integrate_with_bitcoin_value(data, path):
    # Load the Bitcoin dataset
    bitcoin_dataset = pd.read_csv(path)

    # Convert the 'price' column in the dataset to datetime.date format
    bitcoin_dataset['snapped_at'] = pd.to_datetime(bitcoin_dataset['snapped_at'], errors='coerce').dt.date
    # Iterate over the timeseries data
    for index, timeseries in enumerate(data):
        # Extract and normalize the timestamp in the current timeseries to datetime.date
        date = datetime.strptime(timeseries['timestamp'], '%Y-%m-%d').date()
        # Find the matching row in the Bitcoin dataset
        matching_row = bitcoin_dataset[bitcoin_dataset['snapped_at'] == date]
        # If a matching row exists, update the timeseries data
        if not matching_row.empty:
            data[index]['bitcoin_value'] = matching_row.iloc[0]['price']  # Adjust 'bitcoin_value' to the actual column name in your dataset
        else:
            data[index]['bitcoin_value'] = None  # Handle cases where no match is found
    return data


def integrate_with_blockchain_data(data, path):
    # # Load the Bitcoin dataset
    # bitcoin_dataset = pd.read_csv(path)

    # # Convert the 'price' column in the dataset to datetime.date format
    # bitcoin_dataset['snapped_at'] = pd.to_datetime(bitcoin_dataset['snapped_at'], errors='coerce').dt.date
    # # Iterate over the timeseries data
    # for index, timeseries in enumerate(data):
    #     # Extract and normalize the timestamp in the current timeseries to datetime.date
    #     date = datetime.strptime(timeseries['timestamp'], '%Y-%m-%d').date()
    #     # Find the matching row in the Bitcoin dataset
    #     matching_row = bitcoin_dataset[bitcoin_dataset['snapped_at'] == date]
    #     # If a matching row exists, update the timeseries data
    #     if not matching_row.empty:
    #         data[index]['bitcoin_value'] = matching_row.iloc[0]['price']  # Adjust 'bitcoin_value' to the actual column name in your dataset
    #     else:
    #         data[index]['bitcoin_value'] = None  # Handle cases where no match is found
    # return data

    fixed_data = data

    with open(path, 'r') as f2:
        blockchain_data = json.load(f2)

    # Convert blockchain data to a dictionary for quick access by timestamp
    blockchain_dict = {entry['timestamp']: entry for entry in blockchain_data}

    # Merge the data
    for fixed_entry in fixed_data:
        timestamp = fixed_entry['timestamp']
        # If timestamp exists in blockchain_dict, add the fields
        if timestamp in blockchain_dict:
            fixed_entry['no_opened_p2wsh'] = blockchain_dict[timestamp]['no_opened_p2wsh']
            fixed_entry['no_potential_closures'] = blockchain_dict[timestamp]['no_potential_closures']
        else:
            # Add keys with None values if no match found
            fixed_entry['no_opened_p2wsh'] = None
            fixed_entry['no_potential_closures'] = None

    print("Data merging complete. Merged data saved to 'merged_data.json'.")
    return data
    


def load_precomputed_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return None

def create_precomputed_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)



def display_two_curves(data, x_key, y_keys, labels, title, colors):
    """
    Displays a single plot with two curves based on data from the same dataset.
    
    Args:
        data (list): Dataset, a list of dictionaries with keys.
        x_key (str): Key representing the x-axis.
        y_keys (list): Keys representing the y-axis data (one for each curve).
        labels (list): Labels for the two curves.
        title (str): Title of the plot.
        colors (list): Colors for the two curves.
    """
    # Parse dates and y-values
    dates = [datetime.strptime(item[x_key], "%Y-%m-%d") for item in data]
    y_values1 = [item[y_keys[0]] for item in data]
    y_values2 = [item[y_keys[1]] for item in data]

    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)

    # Plot the curves
    ax.plot(dates, y_values1, label=labels[0], color=colors[0], marker="o", markersize=4)
    ax.plot(dates, y_values2, label=labels[1], color=colors[1], marker="s", markersize=4)

    # Set logarithmic y-axis
    ax.set_yscale("log")

    # Add title, grid, and labels
    ax.set_title(title, fontsize=14, pad=10)
    ax.set_ylabel("Values", fontsize=12)
    ax.set_xlabel("Date", fontsize=12)
    ax.grid(True)
    ax.legend(fontsize=10, loc="upper left")

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 12)))
    plt.xticks(rotation=45, fontsize=10)  # Rotate for readability

    # Display the plot
    plt.show()

def display_plot(data, json_keys, labels, titles, colors):
    no_labels = len(labels)
    
    # Adjust number of subplots (merging first two into one)
    adjusted_no_labels = no_labels - 1 if no_labels > 1 else 1
    
    fig_height = max(6, adjusted_no_labels * 3)  # Increased height
    fig, axes = plt.subplots(adjusted_no_labels, 1, figsize=(12, fig_height), sharex=True, constrained_layout=True)
    
    if adjusted_no_labels == 1:
        axes = [axes]
    
    dates = [datetime.strptime(item[json_keys[-1]], "%Y-%m-%d") for item in data]
    
    # Merge the first two plots
    y_values1 = [item[json_keys[0]] for item in data]
    y_values2 = [item[json_keys[1]] for item in data]
    
    axes[0].plot(dates, y_values1, label=labels[0], color=colors[0], marker="o", markersize=5)
    axes[0].plot(dates, y_values2, label=labels[1], color=colors[1], marker="s", markersize=5)
    
    axes[0].set_title(f"{titles[0]} & {titles[1]}", fontsize=max(12, 16 - adjusted_no_labels), pad=15)  # Increased padding
    axes[0].set_ylabel(f"{labels[0]} / {labels[1]}", fontsize=max(10, 14 - adjusted_no_labels))
    axes[0].grid(True)
    axes[0].legend(fontsize=max(8, 12 - adjusted_no_labels), loc="upper left")
    
    # Plot remaining subplots
    for i in range(2, no_labels):
        y_values = [item[json_keys[i]] for item in data]
        axes[i - 1].plot(dates, y_values, label=labels[i], color=colors[i], marker="o", markersize=5)
        
        axes[i - 1].set_title(titles[i], fontsize=max(12, 16 - adjusted_no_labels), pad=15)
        axes[i - 1].set_ylabel(labels[i], fontsize=max(10, 14 - adjusted_no_labels))
        axes[i - 1].grid(True)
        axes[i - 1].legend(fontsize=max(8, 12 - adjusted_no_labels), loc="upper left")
    
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    axes[-1].xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 12)))
    
    plt.xticks(rotation=60, fontsize=max(10, 14 - adjusted_no_labels))  # Increased rotation and font size
    plt.xlabel("Date", fontsize=max(12, 14 - adjusted_no_labels))
    
    fig.tight_layout(h_pad=1.5)  # More space between subplots
    fig.subplots_adjust(top=0.95, bottom=0.15)  # Increased bottom margin
    
    plt.show()

def plot_normalized_histogram(data1, data2, xlabel, ylabel, title):
    """
    Plots a normalized histogram for two data sets.

    Parameters:
        data1 (list): The first dataset.
        data2 (list): The second dataset.
        xlabel (str): Label for the x-axis.
        ylabel (str): Label for the y-axis.
        title (str): Title of the histogram.
    """
    # Ensure the input data are valid lists
    if not isinstance(data1, list) or not isinstance(data2, list):
        raise TypeError("Both data1 and data2 should be lists.")

    # Plot the normalized histogram
    plt.figure(figsize=(10, 6))
    plt.hist(
        [data1, data2], 
        bins=20, 
        density=True,  # Normalizes the histogram
        label=['Dataset 1', 'Dataset 2'], 
        alpha=0.7,  # Transparency
        edgecolor='black'
    )

    # Add labels and title
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    
    # Add legend
    plt.legend()
    
    # Display the plot
    plt.tight_layout()
    plt.show()

def get_no_channels_inside_bitcoin_transaction_distribution(channel_points):
    """
    ---
    """
    grouped_txids = defaultdict(int)
    for entry in channel_points:
        txid, _ = entry.split(':')
        grouped_txids[txid] += 1

    distribution = Counter(grouped_txids.values())
    return sorted(distribution.items())


# Output number distribution (with percentages)
def get_p2wsh_output_number_distribution(on_chain_transactions):
    """
    Compute the distribution of the number of P2WSH outputs in the on-chain transactions.
    """
    # Count the number of P2WSH outputs in each transaction
    num_p2wsh_outputs = [
        sum(1 for vout in tx["transaction"]["vout"] if vout["scriptpubkey_type"] == "v0_p2wsh") 
        for tx in on_chain_transactions
    ]

    distribution = Counter(num_p2wsh_outputs)
    return sorted(distribution.items())


# Output number distribution (with percentages)
def get_p2wsh_output_value_distribution(on_chain_transactions):
    """
    Compute the distribution of the number of P2WSH outputs in the on-chain transactions.
    """
    # Count the number of P2WSH outputs in each transaction
    num_p2wsh_outputs = [
        sum(1 for vout in tx["transaction"]["vout"] if vout["scriptpubkey_type"] == "v0_p2wsh") 
        for tx in on_chain_transactions
    ]

    distribution = Counter(num_p2wsh_outputs)
    return sorted(distribution.items())


def get_richest_p2wsh_output_value_distribution(on_chain_transactions):
    """
    Compute the distribution of the richest P2WSH output value in the on-chain transactions.
    Also computes the percentile of transactions where the richest P2WSH output value is at most 10,000,000.
    """
    # Extract the richest P2WSH output value for each transaction
    richest_p2wsh_values = []
    for tx in on_chain_transactions:
        # Filter P2WSH outputs and get their values
        p2wsh_values = [
            vout["value"] for vout in tx["transaction"]["vout"] if vout["scriptpubkey_type"] == "v0_p2wsh"
        ]
        
        # If there are P2WSH outputs, record the maximum value; otherwise, skip
        if p2wsh_values:
            richest_p2wsh_values.append(max(p2wsh_values))
    if not richest_p2wsh_values:
        return "No P2WSH transactions found."

    # Compute the percentile of transactions with richest P2WSH output ≤ 10,000,000
    threshold = 1_000_000_000
    percentile_below_threshold = percentileofscore(richest_p2wsh_values, threshold, kind='rank')
    print(f"Percentile of transactions with richest P2WSH output ≤ {threshold}: {percentile_below_threshold:.10f}%")

    # Compute the distribution
    distribution = Counter(richest_p2wsh_values)
    
    return sorted(distribution.items())


def calculate_script_type_percentage(transactions, script_type):
    """
    Calculates the percentage of transactions that have an input of the specified scriptpubkey_type.

    Args:
        transactions (list): A list of transactions as dictionaries.
        script_type (str): The scriptpubkey_type to look for in transaction inputs.

    Returns:
        float: The percentage of transactions with the specified scriptpubkey_type in their inputs.
    """
    total_transactions = len(transactions)
    if total_transactions == 0:
        return 0.0

    # Count the transactions matching the specified scriptpubkey_type
    matching_transactions = 0
    for transaction_data in transactions:
        transaction = transaction_data["transaction"]
        for input_data in transaction["vin"]:
            prevout = input_data.get("prevout", {})
            if prevout.get("scriptpubkey_type") == script_type:
                matching_transactions += 1
                break  # Count this transaction and move to the next one

    # Calculate the percentage
    percentage = (matching_transactions / total_transactions) * 100
    return percentage

def calculate_script_type_percentage(transactions, script_types):
    """
    Calculates the percentage of transactions that have an input of the specified scriptpubkey_types.

    Args:
        transactions (list): A list of transactions as dictionaries.
        script_types (list or tuple): The scriptpubkey_types to look for in transaction inputs.

    Returns:
        float: The percentage of transactions with the specified scriptpubkey_types in their inputs.
    """
    total_transactions = len(transactions)
    if total_transactions == 0:
        return 0.0

    # Ensure script_types is a set for faster membership checking
    script_types_set = set(script_types)

    # Count the transactions matching any of the specified scriptpubkey_types
    matching_transactions = 0
    for transaction_data in transactions:
        transaction = transaction_data["transaction"]
        for input_data in transaction["vin"]:
            prevout = input_data.get("prevout", {})
            if prevout.get("scriptpubkey_type") in script_types_set:
                matching_transactions += 1
                break  # Count this transaction and move to the next one

    # Calculate the percentage
    percentage = (matching_transactions / total_transactions) * 100
    return percentage

def calculate_script_combinations_percentages(transactions, script_types):
    """
    Calculates the percentage of transactions that contain inputs matching various combinations 
    of up to 3 scriptpubkey_types.

    Args:
        transactions (list): A list of transactions as dictionaries.
        script_types (set): A set of scriptpubkey_types to generate combinations.

    Returns:
        dict: A dictionary where keys are combinations (as tuples) and values are percentages.
    """
    total_transactions = len(transactions)
    if total_transactions == 0:
        return {}

    # Generate all combinations of the script types from 1 to 3 members
    combinations_percentages = {}

    for r in range(1, 4):  # r is the size of the combination (1, 2, or 3)
        for combo in combinations(script_types, r):
            # Count transactions matching any of the script types in the combination
            combo_set = set(combo)
            matching_transactions = 0
            for transaction_data in transactions:
                transaction = transaction_data["transaction"]
                for input_data in transaction["vin"]:
                    prevout = input_data.get("prevout", {})
                    if prevout.get("scriptpubkey_type") in combo_set:
                        matching_transactions += 1
                        break  # Move to the next transaction once a match is found

            # Calculate the percentage for this combination
            percentage = (matching_transactions / total_transactions) * 100
            combinations_percentages[combo] = percentage

    return combinations_percentages


def get_timestamps(snapshots_name):
    """
    Extract the channel points (on-chain references) from the snapshots of the Lightning Network
    """
    timestamps = []  # Use a separate list to collect timestamps
    for snapshot_name in snapshots_name:  
        print("Parsing LN snapshot: " + snapshot_name)
        with open(DATASET_PATH + snapshot_name, 'r') as file:
            snapshot_data = json.load(file)  # Load the JSON file into snapshot_data
            print("timestamp----")
            print(snapshot_data['timestamp'])
            print("timestamp----")
            timestamps.append(snapshot_data['timestamp'])  # Add the timestamp to the list

    formatted_data = []
    for entry in timestamps:  # Loop over the collected timestamps
        parts = entry.split('_')
        date = '_'.join(parts[:3])
        time = '_'.join(parts[3:])
        x_col = 'X' if time != '00_00' else ''
        formatted_data.append([date, time, x_col])
    
    return pd.DataFrame(formatted_data, columns=['Date', 'Hours', 'X'])

def save_timestamps_to_excel(df, output_path='timestamps.xlsx'):
    """
    Save the given DataFrame to an Excel file.

    Args:
    df (pd.DataFrame): DataFrame containing the timestamps data.
    output_path (str): The path to save the Excel file.
    """
    try:
        df.to_excel(output_path, index=False)
        print(f"Data saved successfully to {output_path}.")
    except Exception as e:
        print(f"An error occurred while saving to Excel: {e}")


def get_p2wsh_output_number_distribution(on_chain_transactions):
    """
    Compute the distribution of the number of P2WSH outputs in the on-chain transactions.
    """
    # Count the number of P2WSH outputs in each transaction
    num_p2wsh_outputs = [
        sum(1 for vout in tx["transaction"]["vout"] if vout["scriptpubkey_type"] == "v0_p2wsh") 
        for tx in on_chain_transactions
    ]

    distribution = Counter(num_p2wsh_outputs)
    return sorted(distribution.items())

def get_ln_channels_balance_distribution(BLOs):
    balances = []
    for blo in BLOs:
        channel_output_index = int(blo['chan_point'].split(':')[1])
        channel_value = blo['transaction']['vout'][channel_output_index]['value']
        balances.append(channel_value) 
    distribution = Counter(balances)
    return sorted(distribution.items())

    

if __name__ == "__main__":
    
    # get channel points
    snapshots_name = os.listdir(DATASET_PATH)
    snapshots_name = sorted(snapshots_name)
    print("Getting channel points...")
    channel_points = []
    if not os.path.exists(CHANNEL_POINTS_PATH):
        channel_points = get_channel_points(snapshots_name)
        create_precomputed_data(CHANNEL_POINTS_PATH, channel_points)
    else:
        channel_points = load_precomputed_data(CHANNEL_POINTS_PATH)
    
    # create a on-chain LN channels file, if it doesn't exist
    transactions_file_path = Path(TRANSACTIONS_FILE_PATH);
    if (not transactions_file_path.exists()):
        print("The transactions file doesn't exist, it will be created... ")
        create_on_chain_transactions_file(channel_points, TRANSACTIONS_FILE_PATH)
    
    # load the on-chain LN channels file
    on_chain_ln_channels = get_on_chain_transactions_list(TRANSACTIONS_FILE_PATH)
    print(on_chain_ln_channels[:1])
    total_closed_channels = {}
    # display opened channels over time
    print("Getting opened channels over time:")
    opened_and_closed_channels_over_time = [] 
    if not os.path.exists(OPENED_AND_CLOSED_CHANNELS_OVER_TIME_PATH):
        opened_and_closed_channels_over_time = get_opened_and_closed_channels_over_time(snapshots_name)
        create_precomputed_data(OPENED_AND_CLOSED_CHANNELS_OVER_TIME_PATH, opened_and_closed_channels_over_time)
    else:
        opened_and_closed_channels_over_time = load_precomputed_data(OPENED_AND_CLOSED_CHANNELS_OVER_TIME_PATH)
    print("Fixing the holes and zeros of the timeseries")
    fixed_data = fix_timeseries(opened_and_closed_channels_over_time, "opened_channels")
    fixed_data = fix_timeseries(fixed_data, "closed_channels")
    bitcoin_value_integrated_data = integrate_with_bitcoin_value(fixed_data, BITCOIN_DATASET_PATH)
    
    blockchain_integrated_data = integrate_with_blockchain_data(bitcoin_value_integrated_data, "opened_and_closed_channels_from_blockchain.json")
    blockchain_integrated_data = fix_timeseries(blockchain_integrated_data, "no_opened_p2wsh")
    blockchain_integrated_data = fix_timeseries(blockchain_integrated_data, "no_potential_closures")


    json_keys = ["opened_channels", "closed_channels", "total_channels", "timestamp"]
    # json_keys = ["opened_channels", "closed_channels", "total_channels", "bitcoin_value", "timestamp"]
    # json_keys = ["opened_channels", "no_opened_p2wsh", "closed_channels", "no_potential_closures", "total_channels", "bitcoin_value", "timestamp"]
    labels = ["Opened Channels", "Closed Channels", "Num Channels"]
    # labels = ["Opened Channels", "Closed Channels", "Total Channels", "Bitcoin Value"]
    # labels = ["Opened Channels", "Potential Opened Channels","Closed Channels", "Potential Closed Channels", "Total Channels", "Bitcoin Value"]
    titles = ["Number of Opened Channels Over Time", "Number of Closed Channels Over Time", "Number of Channels Over Time"]
    # titles = ["Number of Opened Channels Over Time", "Number of Closed Channels Over Time", "Total Number of Channels Over Time", "Bitcoin Value Over Time"]
    # titles = ["Number of Opened Channels Over Time", "Number of Potential Opened Channels Over Time", "Number of Closed Channels Over Time",  "Number of Potential Opened Channels Over Time", "Total Number of Channels Over Time", "Bitcoin Value Over Time"]
    colors = ["green", "red", "blue"]
    # colors = ["green", "red", "blue", "orange"]
    # colors = ["green", "black", "red", "black", "blue", "orange"]
    display_plot(blockchain_integrated_data[1:], json_keys, labels, titles, colors)

    # display opened nodes over time
    print("Getting opened nodes over time:")
    opened_and_closed_nodes_over_time = [] 
    if not os.path.exists(OPENED_AND_CLOSED_NODES_OVER_TIME_PATH):
        opened_and_closed_nodes_over_time = get_opened_and_closed_nodes_over_time(snapshots_name)
        create_precomputed_data(OPENED_AND_CLOSED_NODES_OVER_TIME_PATH, opened_and_closed_nodes_over_time)
    else:
        opened_and_closed_nodes_over_time = load_precomputed_data(OPENED_AND_CLOSED_NODES_OVER_TIME_PATH)
    print("Fixing the holes and zeros of the timeseries")
    fixed_data = fix_timeseries(opened_and_closed_nodes_over_time, "opened_nodes")
    fixed_data = fix_timeseries(fixed_data, "closed_nodes")
    integrated_data = integrate_with_bitcoin_value(fixed_data, BITCOIN_DATASET_PATH)

    json_keys = ["opened_nodes", "closed_nodes", "total_nodes", "timestamp"]
    # json_keys = ["opened_nodes", "closed_nodes", "total_nodes", "bitcoin_value", "timestamp"]
    # json_keys = ["opened_nodes", "closed_nodes", "total_nodes", "bitcoin_value", "timestamp"]
    labels = ["Opened Nodes", "Closed Nodes", "Num Nodes"]
    # labels = ["Opened Nodes", "Closed Nodes", "Num Nodes", "Bitcoin Value"]
    titles = ["Number of Opened Nodes Over Time", "Number of Closed Nodes Over Time", "Number of Nodes Over Time"]
    # titles = ["Number of Opened Nodes Over Time", "Number of Closed Nodes Over Time", "Number of Nodes Over Time", "Bitcoin Value Over Time"]
    colors = ["green", "red", "blue"]
    # colors = ["green", "red", "blue", "orange"]
    display_plot(integrated_data[1:], json_keys, labels, titles, colors)


    ##############################
    

    
    # get the output index distribution of the channel points
    print("\n--- Distribution of the channel output index in BLOs ---")
    index_output_distribution = get_output_index_distribution(channel_points)
    print("Top 5:")
    print_percentage_distribution(index_output_distribution, len(channel_points), 5)
    print("Percentage of transactions with at most 4 as index:")
    print(get_percentage_of_firsts_n_most_frequent_keys(index_output_distribution, len(channel_points), 5))
    print("Percentage of transactions with at most 9 as index:")
    print(get_percentage_of_firsts_n_most_frequent_keys(index_output_distribution, len(channel_points), 10))
    x = [point[0] for point in index_output_distribution]
    y = [point[1] for point in index_output_distribution]

    # Normalize the frequencies
    total = sum(y)
    normalized_y = [value / total for value in y]

    # Plot normalized histogram
    plt.bar(x, normalized_y, color='blue', alpha=0.7)
    plt.title('Distribution of the channel output index in BLOs')
    plt.xlabel('Channel output index')
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    # get the number of outputs distribution of the on chain LN channels 
    print("\n--- Distribution of Output Counts in BLOs ---")
    output_number_distribution = get_output_number_distribution(on_chain_ln_channels)
    print("Top 5:")
    print_percentage_distribution(output_number_distribution, len(on_chain_ln_channels), 5)
    print("Percentage of transactions with at most 5 outputs:")
    print(get_percentage_of_firsts_n_most_frequent_keys(output_number_distribution, len(on_chain_ln_channels), 5))
    print("Percentage of transactions with at most 10 outputs:")
    print(get_percentage_of_firsts_n_most_frequent_keys(output_number_distribution, len(on_chain_ln_channels), 10))
    x = [point[0] for point in output_number_distribution]
    y = [point[1] for point in output_number_distribution]

    # Normalize the frequencies
    total = sum(y)
    normalized_y = [value / total for value in y]

    # Plot normalized histogram
    plt.bar(x, normalized_y, color='blue', alpha=0.7)
    plt.title('Distribution of Output Counts in BLOs')
    plt.xlabel('Number of outputs')
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

    # get the number of inputs distribution of the on chain LN channels 
    print("\n--- Input number distribution ---")
    input_number_distribution = get_input_number_distribution(on_chain_ln_channels)
    print("Top 5:")
    print_percentage_distribution(input_number_distribution, len(on_chain_ln_channels), 5)
    print("Percentage of transactions with at most 5 inputs:")
    print(get_percentage_of_firsts_n_most_frequent_keys(input_number_distribution, len(on_chain_ln_channels), 5))
    print("Percentage of transactions with at most 10 inputs:")
    print(get_percentage_of_firsts_n_most_frequent_keys(input_number_distribution, len(on_chain_ln_channels), 10))
    x = [point[0] for point in input_number_distribution]
    y = [point[1] for point in input_number_distribution]

    # Normalize the frequencies
    total = sum(y)
    normalized_y = [value / total for value in y]

    # Plot normalized histogram
    plt.bar(x, normalized_y, color='blue', alpha=0.7)
    plt.xscale('log')  # Set x-axis to logarithmic scale
    plt.title('Distribution of number of inputs in BLOs')
    plt.xlabel('Number of inputs')  # Adjust label to indicate log scale
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

    print("\n--- Number of channels inside bitcoin trasanctions distribution ---")

    channel_number_inside_bitcoin_transaction_distribution = get_no_channels_inside_bitcoin_transaction_distribution(channel_points)
    print("Top 5:")
    print_percentage_distribution(channel_number_inside_bitcoin_transaction_distribution, len(on_chain_ln_channels), 5)
    print("Percentage of transactions with at most 5 channels:")
    print(get_percentage_of_firsts_n_most_frequent_keys(channel_number_inside_bitcoin_transaction_distribution, len(on_chain_ln_channels), 5))
    print("Percentage of transactions with at most 10 channels:")
    print(get_percentage_of_firsts_n_most_frequent_keys(channel_number_inside_bitcoin_transaction_distribution, len(on_chain_ln_channels), 10))
    x = [point[0] for point in channel_number_inside_bitcoin_transaction_distribution]
    y = [point[1] for point in channel_number_inside_bitcoin_transaction_distribution]

    # Normalize the frequencies
    total = sum(y)
    normalized_y = [value / total for value in y]

    # Plot normalized histogram
    plt.bar(x, normalized_y, color='blue', alpha=0.7)
    # plt.xscale('log')  # Set x-axis to logarithmic scale
    plt.title('Number of channels inside BLOs distribution')
    plt.xlabel('Number of channels')  # Adjust label to indicate log scale
    plt.ylabel('Frequency')
    plt.yscale('log')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()


    print("\n--- Distribution of P2WSH Output Count in BLOs ---")

    p2wsh_output_number_distribution = get_p2wsh_output_number_distribution(on_chain_ln_channels)
    print("Top 5:")
    print_percentage_distribution(p2wsh_output_number_distribution, len(on_chain_ln_channels), 5)
    print("Percentage of transactions with at most 5 P2wsh outputs:")
    print(get_percentage_of_firsts_n_most_frequent_keys(p2wsh_output_number_distribution, len(on_chain_ln_channels), 5))
    print("Percentage of transactions with at most 10 P2wsh outputs:")
    print(get_percentage_of_firsts_n_most_frequent_keys(p2wsh_output_number_distribution, len(on_chain_ln_channels), 10))
    x = [point[0] for point in p2wsh_output_number_distribution]
    y = [point[1] for point in p2wsh_output_number_distribution]

    # Normalize the frequencies
    total = sum(y)
    normalized_y = [value / total for value in y]

    # Plot normalized histogram
    plt.bar(x, normalized_y, color='blue', alpha=0.7)
    # plt.xscale('log')  # Set x-axis to logarithmic scale
    plt.title('Distribution of P2WSH Output Counts in BLOs')
    plt.xlabel('Number of P2WSH outputs')  # Adjust label to indicate log scale
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

    
    ln_channels_balance_distribution = get_ln_channels_balance_distribution(on_chain_ln_channels)
    print("Top 5:")
    print_percentage_distribution(ln_channels_balance_distribution, len(on_chain_ln_channels), 5)

    # Extract x (balance values in satoshis) and y (frequencies) from the distribution
    x = [point[0] for point in ln_channels_balance_distribution]
    y = [point[1] for point in ln_channels_balance_distribution]

    # Scale factor for converting satoshis to BTC
    scale_factor = 1e8

    # Convert x values from satoshi to BTC
    x_in_btc = [point / scale_factor for point in x]

    # Process richest_p2wsh_output_value_distribution
    values, frequencies = zip(*ln_channels_balance_distribution)

    # Determine bins for the histogram
    bin_count = 20  # Number of bins
    bin_edges = np.linspace(min(values), max(values), bin_count + 1)

    # Scale bin edges for the x-axis (convert from satoshis to BTC)
    scaled_bin_edges = bin_edges / scale_factor

    # Sum up frequencies in each bin
    hist, _ = np.histogram(values, bins=bin_edges, weights=frequencies)

    # Combine bins with frequencies for display
    binned_data = list(zip(scaled_bin_edges[:-1], scaled_bin_edges[1:], hist))

    # Normalize the histogram (sum of frequencies across all bins)
    total = sum(hist)
    normalized_hist = hist / total

    # Plot the histogram using the binned data
    plt.bar(
        scaled_bin_edges[:-1],  # Start of each scaled bin in BTC
        normalized_hist,  # Height of bars
        width=np.diff(scaled_bin_edges),  # Scaled width of each bar in BTC
        color='blue',
        alpha=0.7,
        align='edge'  # Align bars with bin edges
    )

    # Set logarithmic scale for y-axis
    plt.yscale('log')

    # Titles and labels
    plt.title('Lightning Network Balance Distribution')
    plt.xlabel('Balance (BTC)')  # x-axis now in BTC
    plt.ylabel('Frequency')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show the plot
    plt.show()


    # print("\n--- Richest P2WSH output value distribution ---")
    
    # richest_p2wsh_output_value_distribution = get_richest_p2wsh_output_value_distribution(on_chain_ln_channels)
    # print("Top 5:")
    # print_percentage_distribution(richest_p2wsh_output_value_distribution, len(on_chain_ln_channels), 5)
    # print("Top 5:")
    # print_percentage_distribution(richest_p2wsh_output_value_distribution, len(on_chain_ln_channels), 5)
    # print("Percentage of transactions with at most 5 P2wsh outputs:")
    # print(get_percentage_of_firsts_n_most_frequent_keys(richest_p2wsh_output_value_distribution, len(on_chain_ln_channels), 5))
    # print("Percentage of transactions with at most 10 P2wsh outputs:")
    # print(get_percentage_of_firsts_n_most_frequent_keys(richest_p2wsh_output_value_distribution, len(on_chain_ln_channels), 10))
    # # Process richest_p2wsh_output_value_distribution
    # # Scale factor for x-axis values
    # scale_factor = 1e8
 
    # # Process richest_p2wsh_output_value_distribution
    # x = [point[0] for point in richest_p2wsh_output_value_distribution]
    # y = [point[1] for point in richest_p2wsh_output_value_distribution]

    # # Convert to arrays for easier manipulation
    # values, frequencies = zip(*richest_p2wsh_output_value_distribution)

    # # Determine bins
    # bin_count = 20  # Number of bins
    # bin_edges = np.linspace(min(values), max(values), bin_count + 1)

    # # Scale bin edges for the x-axis
    # scaled_bin_edges = bin_edges / scale_factor

    # # Sum up frequencies in each bin
    # hist, _ = np.histogram(values, bins=bin_edges, weights=frequencies)

    # # Combine bins with frequencies for display
    # binned_data = list(zip(scaled_bin_edges[:-1], scaled_bin_edges[1:], hist))

    # # Normalize the histogram (sum of frequencies across all bins)
    # total = sum(hist)
    # normalized_hist = hist / total

    # # Plot the histogram using the binned data
    # plt.bar(
    #     scaled_bin_edges[:-1],  # Start of each scaled bin
    #     normalized_hist,  # Height of bars
    #     width=np.diff(scaled_bin_edges),  # Scaled width of each bar
    #     color='blue',
    #     alpha=0.7,
    #     align='edge'  # Align bars with bin edges
    # )

    # Set logarithmic scale for y-axis
    # plt.yscale('log')

    # Titles and labels
    # plt.title('Richest p2wsh output value distribution')
    # plt.xlabel('Bitcoin')
    # plt.ylabel('Normalized Frequency')
    # plt.grid(axis='y', linestyle='--', alpha=0.7)

    # # Show the plot
    # plt.show()
    
    print("Get the usage of script types in the inputs:")
    script_types = get_script_types(on_chain_ln_channels)
    print(calculate_script_type_percentage(on_chain_ln_channels, ["v0_p2wsh","v0_p2wpkh"]))

    percentages = calculate_script_combinations_percentages(on_chain_ln_channels, script_types)
    for combo, percentage in percentages.items():
        print(f"Combination: {combo}, Percentage: {percentage:.2f}%")


    # display_plot(integrated_data[1:], json_keys, labels, titles, colors)
    display_two_curves(blockchain_integrated_data[1:],  
    x_key="timestamp",
    y_keys=["opened_channels", "no_opened_p2wsh"],
    labels=["Opened channels", "Potential opened channels"],
    title="Upperbound of the number of opened channels",
    colors=["green", "black"])

    display_two_curves(blockchain_integrated_data[1:],  
    x_key="timestamp",
    y_keys=["closed_channels", "no_potential_closures"],
    labels=["Closed channels", "Potential closed channels"],
    title="Upperbound of the number of closed channels",
    colors=["red", "black"])




    

