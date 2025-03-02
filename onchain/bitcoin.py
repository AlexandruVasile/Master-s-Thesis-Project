from bitcoinrpc.authproxy import AuthServiceProxy
import os
import json
import datetime as dt
import time
from decimal import Decimal
# from datetime import datetime as dt2

# constants
DATASET_PATH = '../data/'
TIMESTAMP_TO_BLOCK_HEIGHT_MAPPING_PATH = './precomputed_data/timestamp_to_block_height_mapping.json'
BITCOIN_BLOCKS_PATH = './precomputed_data/bitcoin_blocks/'


# RPC credentials from bitcoin.conf of the Bitcoin node
rpc_user = "ivxga"  
rpc_password = "ivxga" 
rpc_host = "127.0.0.1"  
rpc_port = "8332"       
rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"

# connect to the Bitcoin node
rpc_connection = AuthServiceProxy(rpc_url)

# function to get transactions from a block
def get_transactions_from_block(block_height , last_block):
    # get the block hash for the given height
    block_hash = rpc_connection.getblockhash(block_height)
    block = rpc_connection.getblock(block_hash)

    # fetch transactions using block hash as context
    transactions = []
    no_txs = len(block["tx"])
    for index, txid in enumerate(block["tx"]):
        print(f"{index}/{no_txs} Getting tx {txid} from the block {block_height} of {last_block}")
        transaction = rpc_connection.getrawtransaction(txid, True, block_hash)
        transactions.append(transaction)
    return transactions

def count_p2wsh_outputs(bitcoin_block):
    """
    Count the number of Pay-to-Witness-Script-Hash (P2WSH) outputs in a set of transactions.

    Args:
        data (list): List of transaction dictionaries.

    Returns:
        int: The total number of P2WSH outputs.
    """
    count = 0

    for tx in bitcoin_block:
        for vout in tx.get('vout', []):
            script_pubkey = vout.get('scriptPubKey', {})
            if script_pubkey.get('type') == 'witness_v0_scripthash':
                count += 1
    print(count)
    return count




def convert_to_date(iso_string): 
    """
    Converts a string in the format 'YYYY_MM_DD_HH_mm' to 'YYYY-MM-DD'.

    :param iso_string: Input string in the format 'YYYY_MM_DD_HH_mm'
    :return: Converted string in the format 'YYYY-MM-DD'
    """
    try:
        # Parse the input string
        date_obj = dt.datetime.strptime(iso_string, "%Y_%m_%d_%H_%M")
        # Format to 'YYYY-MM-DD'
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format, expected 'YYYY_MM_DD_HH_mm'")


def get_snapshots_timestamps(path):
    res = []
    snapshots_name = os.listdir(DATASET_PATH)
    snapshots_name = sorted(snapshots_name)

    for snapshot_name in snapshots_name:
        snapshot = {}
        print("Parsing the snapshot "+snapshot_name+"...")

        snapshot_path = DATASET_PATH+snapshot_name
        if os.path.exists(snapshot_path):
            with open(snapshot_path, 'r') as file:
                snapshot = json.load(file)
            if snapshot.get("timestamp") is not None:
                timestamp = snapshot['timestamp']
            else:
                parts = snapshot_name.split('_')
                # Extract the date part (YYYY_MM_DD)
                timestamp = "_".join(parts[2:5])
                timestamp += "_00_00"
            res.append(timestamp)
    return res

# function to convert timestamp string like '2024_11_02_00_00' into UNIX timestamp
def convert_to_unix_timestamp(timestamp_str):
    return int(time.mktime(dt.datetime.strptime(timestamp_str, "%Y_%m_%d_%H_%M").timetuple()))


# get current block height and timestamp
def get_block_height_for_timestamp(timestamp):
    print("Getting block height relative to the timestamp "+ str(timestamp))
    block_height = rpc_connection.getblockcount()
    for height in range(block_height, 0, -1):
        block = rpc_connection.getblock(rpc_connection.getblockhash(height))
        block_time = block['time']  # the time for the block in UNIX timestamp
        print(f"Height: {height}, Timestamp: {dt.datetime.fromtimestamp(block['time'])}")

        
        if block_time <= timestamp:  # find the closest block before or equal to the timestamp
            return height
    return None


def map_timestamp_to_block_height(timestamps, first_block_height):
    res = []
    current_height = first_block_height
    res.append({"timestamp":timestamps[0], "height": first_block_height})
    for timestamp in timestamps[1:]:
        while True:
            print(f"Trying height {current_height}")
            unix_timestamp = convert_to_unix_timestamp(timestamp)
            block = rpc_connection.getblock(rpc_connection.getblockhash(current_height))
            block_time = block['time']  # the time for the block in UNIX timestamp
            if block_time >= unix_timestamp:  # find the closest block before or equal to the timestamp
                print(current_height)
                break
            current_height += 1
        
        res.append({"timestamp": timestamp, "height": current_height})
    return res

        
def load_precomputed_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return None

def create_precomputed_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, default=decimal_default)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")



def get_transaction_by_hash(txid):
    """
    Retrieves the details of a specific transaction from the Bitcoin blockchain.

    Args:
        txid (str): The transaction hash.

    Returns:
        dict: The details of the transaction as a dictionary, or None if the transaction is not found.
    """
    try:
        # fetch the transaction details
        transaction = rpc_connection.getrawtransaction(txid, True)
        return transaction
    except Exception as e:
        print(f"Error retrieving transaction {txid}: {e}")
        return None


def is_2of2_multisig(txinwitness):
    """
    Determines if a txinwitness corresponds to a 2-of-2 multisignature script.
    
    Args:
        txinwitness (list): The witness stack from the transaction input.
    
    Returns:
        bool: True if the witness stack corresponds to a 2-of-2 multisignature, False otherwise.
    """
    if not isinstance(txinwitness, list) or len(txinwitness) < 3:
        return False
    
    # A 2-of-2 multisig stack should consist of two signatures and a redeem script
    sig1, sig2, script = txinwitness[-3], txinwitness[-2], txinwitness[-1]
    
    try:
        # Decode the script to check for multisig pattern
        script_bytes = bytes.fromhex(script)

        # Verify multisig structure:
        # 1. OP_2 (0x52) for 2 required signatures
        # 2. Exactly 2 public keys, each 33 bytes or 65 bytes (compressed/uncompressed)
        # 3. OP_2 (0x52) to declare 2 public keys
        # 4. OP_CHECKMULTISIG (0xae)
        if (script_bytes[:1] == b'\x52' and                # OP_2 for 2 required signatures
            script_bytes[-1:] == b'\xae' and               # OP_CHECKMULTISIG
            script_bytes[-2:-1] == b'\x52'):               # OP_2 for 2 public keys
            
            # Extract and count public keys in the script
            pubkeys = script_bytes[1:-2]  # Strip leading and trailing opcodes
            public_key_count = 0
            i = 0
            while i < len(pubkeys):
                length = pubkeys[i]       # Key length (first byte of key)
                if length not in (33, 65):  # Only compressed or uncompressed keys
                    return False
                i += 1 + length           # Move to next key
                public_key_count += 1
            
            if public_key_count == 2:    # Exactly 2 public keys
                return True
    except ValueError:
        # Invalid hex data in the redeem script
        return False
    return False


def count_potential_closing_tx(bitcoin_block, log_file="multisig_log.txt"):
    """
    Count the number of Pay-to-Witness-Script-Hash (P2WSH) outputs in a set of transactions,
    filtering for transactions related to 2-of-2 multisignature scripts.
    Additionally, log the txinwitness to a file each time a 2-of-2 multisignature transaction is identified.
    
    Args:
        bitcoin_block (list): List of transaction dictionaries.
        log_file (str): Path to the log file where txinwitness is written.
    
    Returns:
        int: The total number of potential closing transactions.
    """
    count = 0
    with open(log_file, "a") as file:  # open file in append mode
        for tx in bitcoin_block:
            vins = tx.get('vin', [])
            if len(vins) == 1:
                txinwitness = vins[0].get('txinwitness', None)  # Safely get 'txinwitness'
                if txinwitness is not None:  # Only proceed if 'txinwitness' exists
                    is_multisig = is_2of2_multisig(txinwitness)
                    if is_multisig:
                        # Log the txinwitness to the file
                        file.write(f"{txinwitness}\n")
                        count += 1        
    return count


def get_hours_distance(timestamp1, timestamp2):
    if not timestamp1 or not timestamp2:  # check if either timestamp is an empty string
        return -1
    
    format_str = "%Y_%m_%d_%H_%M"  # define the expected format
    dt1 = dt.datetime.strptime(timestamp1, format_str)
    dt2 = dt.datetime.strptime(timestamp2, format_str)
    res = abs((dt2 - dt1).total_seconds() / 60 / 60)  # calculate absolute difference in hours
    return res

if __name__ == "__main__":
    timestamp_to_block_height_mapping = load_precomputed_data(TIMESTAMP_TO_BLOCK_HEIGHT_MAPPING_PATH)
    
    # create the mapping in case it doesn't exist
    if timestamp_to_block_height_mapping == None:
        timestamps = get_snapshots_timestamps(DATASET_PATH)
        print("xxxxx")
        print(timestamps)
        print("xxxxx")
        unix_timestamp = convert_to_unix_timestamp(timestamps[0])
        print("Getting the first block height..")
        #first_block_height = get_block_height_for_timestamp(unix_timestamp)
        first_block_height = 868474

        timestamp_to_block_height_mapping = map_timestamp_to_block_height(timestamps, first_block_height)
        # save the mapping in a file
        create_precomputed_data(TIMESTAMP_TO_BLOCK_HEIGHT_MAPPING_PATH, timestamp_to_block_height_mapping)
        

    upperbound_opened_and_channels_over_time = []

    no_timestamps = len(timestamp_to_block_height_mapping)
    current_height = timestamp_to_block_height_mapping[0]["height"]
    
    print("No timestamps:")
    print(no_timestamps)
    print("Current height:")
    print(current_height)
    print("Range value:")
    print(no_timestamps - 2)



    for index in range(no_timestamps-1):
        next_height = timestamp_to_block_height_mapping[index+1]["height"]
        p2wsh_outputs_counter = 0
        potential_closing_tx_counter = 0
        last_block = timestamp_to_block_height_mapping[-1]["height"]
        while current_height < next_height and index < (no_timestamps - 2):
            print("---")
            print("next_height "+str(next_height))
            print("current_height "+str(current_height))
            print("index" +str(index))
            print("---")
            bitcoin_block  = load_precomputed_data(BITCOIN_BLOCKS_PATH+str(current_height)+".json")
            # print(bitcoin_block)
            if bitcoin_block == None:
                bitcoin_block = get_transactions_from_block(current_height, last_block)
                create_precomputed_data(BITCOIN_BLOCKS_PATH+str(current_height)+".json", bitcoin_block)
            p2wsh_outputs_counter += count_p2wsh_outputs(bitcoin_block)
            potential_closing_tx_counter += count_potential_closing_tx(bitcoin_block)
            current_height += 1 
        # add upperbound entry
        current_timestamp = timestamp_to_block_height_mapping[index]['timestamp']
        next_timestamp = timestamp_to_block_height_mapping[index + 1]['timestamp']
        hours_distance = get_hours_distance(current_timestamp, next_timestamp)
        upperbound_opened_and_channels_over_time.append({"timestamp": convert_to_date(timestamp_to_block_height_mapping[index + 1]['timestamp']), "no_opened_p2wsh": p2wsh_outputs_counter/hours_distance, "no_potential_closures": potential_closing_tx_counter/hours_distance})
        print(upperbound_opened_and_channels_over_time)

        # Write to the file after appending the latest data
        try:
            with open("opened_and_closed_channels_from_blockchain.json", 'w') as file:
                # Append new entry to the file
                json.dump(upperbound_opened_and_channels_over_time, file)
        except IOError as e:
            print(f"Error writing to file: {e}")
    


    # bitcoin_block  = load_precomputed_data(BITCOIN_BLOCKS_PATH+str(868474)+".json")
    # # print(bitcoin_block)
    # if bitcoin_block == None:
    #     bitcoin_block = get_transactions_from_block(868474)
    #     create_precomputed_data(BITCOIN_BLOCKS_PATH+str(868474)+".json", bitcoin_block)

    # count_p2wsh_outputs(bitcoin_block)
    