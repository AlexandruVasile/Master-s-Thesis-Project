#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

# Create a temporary Python file
PYTHON_SCRIPT="ln_analysis.py"

cat > $PYTHON_SCRIPT <<EOF
import json
import os

DATASET_PATH = './'

def get_opened_and_closed_channels_over_time(snapshots_name):
    previous_channel_points = set()
    measurements = []
    for snapshot_name in sorted(snapshots_name):
        print(f"Parsing LN snapshot: {snapshot_name}")
        with open(DATASET_PATH + snapshot_name, 'r') as file:
            data = json.load(file)
        current_channel_points = {channel['chan_point'] for channel in data['edges']}
        opened_channels = current_channel_points - previous_channel_points
        closed_channels = previous_channel_points - current_channel_points
        measurements.append({
            "snapshot_name": snapshot_name,
            "opened_channels": len(opened_channels),
            "closed_channels": len(closed_channels),
            "total_channels": len(data['edges'])
        })
        previous_channel_points = current_channel_points
    return measurements

if __name__ == "__main__":
    snapshots_name = os.listdir(DATASET_PATH)
    snapshots_name = [name for name in snapshots_name if name.endswith(".json")]
    data = get_opened_and_closed_channels_over_time(snapshots_name)
    
    print("\nLightning Network Channel Analysis:")
    print("=" * 50)
    print(f"{'Snapshot Name':<30}{'Opened':<10}{'Closed':<10}{'Total':<10}")
    print("-" * 50)
    for entry in data:
        print(f"{entry['snapshot_name']:<30} {entry['opened_channels']:<10}{entry['closed_channels']:<10}{entry['total_channels']:<10}")
    print("=" * 50)
EOF

# Run the Python script
echo "Running the Lightning Network Analysis..."
python3 $PYTHON_SCRIPT

# Clean up
echo "Cleaning up temporary files..."
rm -f $PYTHON_SCRIPT
echo "Done!"
