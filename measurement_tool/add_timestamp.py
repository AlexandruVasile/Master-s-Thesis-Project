import os
import re
import json
import argparse

def process_json_file(file_path):
    # regular expression pattern to match the file naming convention
    pattern = r"network_graph_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})\.json"
    
    # extract file name from the path
    file_name = os.path.basename(file_path)
    
    match = re.match(pattern, file_name)
    if match:
        # extract the date, hour, and minute from the file name
        year = match.group(1)
        month = match.group(2)
        day = match.group(3)
        hour = match.group(4)
        minute = match.group(5)
        timestamp = f"{year}_{month}_{day}_{hour}_{minute}"
        
        try:
            # load the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)
            
            # add or update the "timestamp" key with the extracted value
            data['timestamp'] = timestamp
            
            # write the updated JSON back to the file
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            
            # create the new file name without hour and minute
            new_file_name = f"network_graph_{year}_{month}_{day}.json"
            new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
            os.rename(file_path, new_file_path)
            
            print(f"Updated and renamed file: {file_name} to {new_file_name} with timestamp: {timestamp}")
        
        except Exception as e:
            print(f"Failed to process {file_name}: {e}")
    else:
        print(f"File {file_name} does not match the expected naming pattern.")

# command-line argument handling
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a network graph JSON file.")
    parser.add_argument("file", help="Path to the network graph JSON file to process")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call the function with the provided file path
    process_json_file(args.file)

