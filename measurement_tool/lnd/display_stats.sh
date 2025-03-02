#!/bin/bash

# Check if folder is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <folder_path>"
  exit 1
fi

# Assign the folder path to a variable, quoted to handle spaces
FOLDER_PATH="$1"

# Temporary file to store counts for graphing
GRAPH_DATA_FILE="/tmp/graph_data.csv"
echo "date,pub_key_count,channel_id_count" > "$GRAPH_DATA_FILE"

# Loop through each JSON file in the specified folder
for file in "$FOLDER_PATH"/*.json; do
  # Check if there are any matching files
  if [ ! -e "$file" ]; then
    echo "No matching .json files found in the specified folder."
    exit 1
  fi

  # Extract the date from the filename (snapshot_YYYY-MM-DD_HH-MM.json)
  filename=$(basename "$file")
  date=$(echo "$filename" | sed -E 's/snapshot_([0-9]{4}-[0-9]{2}-[0-9]{2})_.*/\1/')

  # Count occurrences of "pub_key"
  pub_key_count=$(grep -o "pub_key" "$file" | wc -l)

  # Count occurrences of "channel_id"
  channel_id_count=$(grep -o "channel_id" "$file" | wc -l)

  # Append results to the graph data file
  echo "$date,$pub_key_count,$channel_id_count" >> "$GRAPH_DATA_FILE"

  # Display results
  echo "File: $filename"
  echo "Date: $date"
  echo "pub_key count: $pub_key_count"
  echo "channel_id count: $channel_id_count"
  echo
done

# Generate graph using Python
python3 <<EOF
import matplotlib.pyplot as plt
import pandas as pd

# Load the data
data = pd.read_csv("$GRAPH_DATA_FILE")

# Debug: Print the data to ensure it's loaded correctly
print("Loaded data:")
print(data)

# Convert the 'date' column to a pandas datetime object
data['date'] = pd.to_datetime(data['date'], errors='coerce')

# Debug: Check data after date conversion
print("\nData after converting 'date':")
print(data)

# Drop rows with invalid or missing dates
data = data.dropna(subset=['date'])

# Ensure count columns are numeric
data['pub_key_count'] = pd.to_numeric(data['pub_key_count'], errors='coerce').fillna(0).astype(int)
data['channel_id_count'] = pd.to_numeric(data['channel_id_count'], errors='coerce').fillna(0).astype(int)

# Debug: Final data structure before plotting
print("\nFinal cleaned data:")
print(data)

# Sort the data by date
data = data.sort_values('date')

# Plot pub_key counts
plt.figure(figsize=(10, 6))
plt.plot(data['date'].values, data['pub_key_count'].values, marker='o', label='pub_key Count', color='blue')
plt.xticks(rotation=45, ha='right')
plt.xlabel('Date')
plt.ylabel('Count')
plt.title('pub_key Counts Over Time')
plt.grid(True)
plt.tight_layout()
plt.savefig("$FOLDER_PATH/pub_key_counts.png")
print(f"Graph saved to $FOLDER_PATH/pub_key_counts.png")

# Plot channel_id counts
plt.figure(figsize=(10, 6))
plt.plot(data['date'].values, data['channel_id_count'].values, marker='o', label='channel_id Count', color='orange')
plt.xticks(rotation=45, ha='right')
plt.xlabel('Date')
plt.ylabel('Count')
plt.title('channel_id Counts Over Time')
plt.grid(True)
plt.tight_layout()
plt.savefig("$FOLDER_PATH/channel_id_counts.png")
print(f"Graph saved to $FOLDER_PATH/channel_id_counts.png")
EOF
