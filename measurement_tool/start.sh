#!/usr/bin/env bash

# record the start time
start_time=$(date +%s)

bitcoind -datadir=/bitcoind_data > /dev/null 2>&1 &

# wait for bitcoind to start
echo "Waiting for bitcoind to start..."
sleep 10

# tail the debug.log file to see real-time logs while syncing, in the background
tail -f /bitcoind_data/debug.log &
TAIL_PID=$!  # capture the process ID of the tail command

# loop that checks the synchronization progress using bitcoin-cli
while true; do
    # check if bitcoin-cli can communicate with bitcoind
    sync_progress=$(bitcoin-cli -datadir=/bitcoind_data getblockchaininfo 2>/dev/null | jq -r .verificationprogress)
    
    # Check if sync_progress was retrieved and is valid
    if [[ -n "$sync_progress" && "$sync_progress" != "null" ]]; then
        # Convert to a float and check if progress is near 1.0
        if (( $(echo "$sync_progress >= 0.9999" | bc -l) )); then
            echo "Synchronization completed with progress=${sync_progress}!"
            break
        fi
        echo "Current progress: $sync_progress"
    else
        echo "Waiting for bitcoind to be ready..."
    fi

    # Wait before checking again
    sleep 5
done

# kill the tail process after synchronization completes
kill "$TAIL_PID"

# continue with the rest of the script
echo "Waiting lnd to start..."

lnd --lnddir=/lnd_data > /dev/null 2>&1 &


# loop until lncli unlock command output is "LOCKED" or "NON_EXISTING"
while true; do
    # Capture the output of the lncli command
    output=$(lncli --lnddir=/lnd_data state 2>/dev/null)

    # Use jq to parse and get the "state" field
    state=$(echo "$output" | jq -r .state)

    # Check if the state matches "LOCKED" or "NON_EXISTING"
    if [[ "$state" == "LOCKED" || "$state" == "NON_EXISTING" ]]; then
        #echo "Exiting loop. lncli state is: $state"
        break  # Exit the loop if state is one of the target states
    fi

    # Wait before the next check
    sleep 5
done

# Use jq to extract the "state" field from output
state=$(echo "$output" | jq -r .state)

# Check if state is equal to "NON_EXISTING"
if [[ "$state" == "NON_EXISTING" ]]; then
    echo "Creating the wallet..."
    ./create_wallet.sh
else
    echo "Unlocking the wallet..."
    ./unlock.sh
fi


# Variable to track if conditions were met for user prompt
conditions_met=false
echo ""
echo "Preparing for the snapshot, this could take, the first time, also a week depending on your connection"
echo "You will be prompted to take a snapshot when the graph and the blockchain will be synced and five minutes will be passed"
echo ""


while true; do
    # Get LND info and extract the relevant fields
    lnd_info=$(lncli --lnddir=/lnd_data getinfo | jq -r '{synced_to_chain, synced_to_graph}')
    # Get Lightning Network info and extract the relevant fields
    ln_network_info=$(lncli --lnddir=/lnd_data getnetworkinfo | jq -r '{num_nodes, num_channels}')

    # Extract values
    synced_to_chain=$(echo "$lnd_info" | jq -r .synced_to_chain)
    synced_to_graph=$(echo "$lnd_info" | jq -r .synced_to_graph)
    num_nodes=$(echo "$ln_network_info" | jq -r .num_nodes)
    num_channels=$(echo "$ln_network_info" | jq -r .num_channels)

    # Format and print the combined output
    echo "LN info: \"synced_to_chain\": $synced_to_chain, \"synced_to_graph\": $synced_to_graph, \"num_nodes\": $num_nodes, \"num_channels\": $num_channels"

    # Check if both synced_to_chain and synced_to_graph are true
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if [[ $elapsed_time -ge 300 && "$synced_to_chain" == "true" && "$synced_to_graph" == "true" ]]; then
        conditions_met=true
    else
        conditions_met=false
    fi

    # Check if it's 00:00 UTC
    current_utc_time=$(date -u +"%H:%M")
    if [[ "$current_utc_time" == "00:00" ]]; then
        echo "It's 00:00 UTC, taking a snapshot."
        instant=$(date -u +"%Y_%m_%d_%H_%M")
        lncli --lnddir=/lnd_data describegraph > "/lnd_data/network_graph_${instant}.json"
        
        echo "Snapshot saved as network_graph_${instant}.json"

        # Reset start_time to avoid multiple snapshots within the same minute
        start_time=$(date +%s)
        
        # compress the snapshot after 1 minute
        echo "Compression of the snapshot will start after 60 seconds.."
        sleep 60
        python3 compress_snapshot.py --snapshot_path "/lnd_data/network_graph_${instant}.json" --overwrite
        echo "Compression done"
    fi

    # If conditions are met, prompt the user
    if [[ "$conditions_met" == "true" ]]; then
        echo "Conditions met: synced_to_chain and synced_to_graph are true."
        echo "Press 'x' and Enter to execute 'lncli describegraph'."
        
        # Use read with a timeout of 10 seconds
        read -t 10 -n 1 input
        if [[ "$input" == "x" ]]; then
            instant=$(date -u +"%Y_%m_%d_%H_%M")
            echo "Executing lncli describegraph as requested by user."
            lncli --lnddir=/lnd_data describegraph > "/lnd_data/network_graph_${instant}.json"
            echo "Snapshot saved as network_graph_${instant}.json"
            # Reset the timer after execution
            start_time=$(date +%s)
            # compress the snapshot after 1 minute
            echo "Compression of the snapshot will start after 60 seconds.."
            sleep 60
            python3 compress_snapshot.py --snapshot_path "/lnd_data/network_graph_${instant}.json" --overwrite
            echo "Compression done"
        fi
    else
        echo "Conditions not met yet (synced_to_chain == true && synced_to_graph == true && time_passed >= 5 minutes ), waiting for the next check..."
    fi

    # Display the last line of the Bitcoin debug log
    if [[ -f /bitcoind_data/debug.log ]]; then
        last_bitcoin_log=$(tail -n 1 /bitcoind_data/debug.log)
        echo "Last Bitcoin Node's log: $last_bitcoin_log"
    else
        echo "Bitcoin debug.log not found."
    fi

    # Display the last line of the LND log
    if [[ -f /lnd_data/logs/bitcoin/mainnet/lnd.log ]]; then
        last_lnd_log=$(tail -n 1 /lnd_data/logs/bitcoin/mainnet/lnd.log)
        echo "Last LND's log: $last_lnd_log"
    else
        echo "LND log not found."
    fi

    # Sleep to control the loop speed
    sleep 10
    echo ""
done

tail -f /dev/null


