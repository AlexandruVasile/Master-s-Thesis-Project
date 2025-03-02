import json
import re
import os
import argparse

def json_to_single_line(input_file, overwrite):
    
    try:
        # try reading the JSON file with UTF-8 encoding
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # if UTF-8 decoding fails, try UTF-16
        with open(input_file, 'r', encoding='utf-16') as f:
            data = json.load(f)

    # regular expression pattern to match the file naming convention
    pattern = r"network_graph_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})\.json"
    # extract file name from the path
    file_name = os.path.basename(input_file)
    file_dir = os.path.dirname(input_file)
    match = re.match(pattern, file_name)
    year = match.group(1)
    month = match.group(2)
    day = match.group(3)
    hour = match.group(4)
    minute = match.group(5)
    timestamp = f"{year}_{month}_{day}_{hour}_{minute}"
    new_file_name = f"network_graph_{year}_{month}_{day}.json"
    compressed_name = f"network_graph_{year}_{month}_{day}_compressed.json"


    # add timestamp 
    data['timestamp'] = timestamp

    # convert the JSON object to a single line JSON string
    single_line_json = json.dumps(data, separators=(',', ':'))

    # write the single-line JSON to the output file
    compressed_file = os.path.join(file_dir, compressed_name)
    

    with open(compressed_file, 'w', encoding='utf-8') as f:
        f.write(single_line_json)
    if overwrite:
        os.remove(input_file)
        os.rename(compressed_file, os.path.join(file_dir, new_file_name))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON LN snapshot to single-line format.")
    parser.add_argument('--snapshot_path', required=True, type=str, help='Path to the LN snapshot to be compressed')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite the LN snapshot with the compressed version (default: False)')

    args = parser.parse_args()
    json_to_single_line(args.snapshot_path, args.overwrite)