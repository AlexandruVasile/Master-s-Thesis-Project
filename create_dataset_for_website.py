import os
import re
import json
from datetime import datetime
import pandas as pd
import re
from pathlib import Path
from os import listdir
from os.path import isfile
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import json
import csv
from datetime import datetime

DATA_FOLDER = os.path.join('.', 'data')
OUTPUT_FOLDER = os.path.join('.', 'output')
WEBSITE_DATA_FOLDER = os.path.join('.', 'elenvisualizations', 'website_data')
AUX_DATA_FOLDER_NAME = "aux_data"
DIAMETER_DATASET = "diameter.csv"
GC_SIZE_DATESET = "gc_size.csv"

DOWNLOAD_TIMEOUT = 30 # seconds
DOWNLOAD_DIRECTORY = os.path.join(os.getcwd(), 'elenvisualizations', 'website_data', 'aux_data') # where the downloaded datasets will reside

TRANSACTION_COUNT_DATASET_URL = "https://blockchair.com/bitcoin/charts/transaction-count"
TRANSACTION_COUNT_DATASET_DEFAULT_NAME = "data.tsv"
TRANSACTION_COUNT_DATASET_NEW_NAME = "transactions_per_day.tsv"
TRANSACTION_COUNT_DATASET_BUTTON_ID = "download-tsv-button"


FEES_PER_TRANSACTION_DATASET_URL = "https://www.blockchain.com/explorer/charts/fees-usd-per-transaction"
FEES_PER_TRANSACTION_DATASET_DEFAULT_NAME = "fees-usd-per-transaction.json"  
FEES_PER_TRANSACTION_DATASET_NEW_NAME = "fees_per_transaction.csv"
FEES_PER_TRANSACTION_DATASET_DOWNLOAD_BUTTON_CLASS_NAME = "XhALK"
FEES_PER_TRANSACTION_DATASET_3Y_BUTTON_XPATH = "/html/body/div[1]/div[2]/div[2]/main/div/div/div/section[1]/section/div/div[6]/div/button[5]"

BITCOIN_VALUE_DATASET_URL = "https://www.coingecko.com/price_charts/export/1/usd.csv"
BITCOIN_VALUE_DATASET_DEFAULT_NAME = "btc-usd-max.csv" 
BITCOIN_VALUE_DATASET_NEW_NAME = "price_market_per_day.csv"

# configure Selenium WebDriver
options = webdriver.ChromeOptions()
prefs = {"download.default_directory": DOWNLOAD_DIRECTORY, "profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

def convert_json_to_csv(json_filename, csv_filename):
    """
    Reads data from a JSON file and converts it into a CSV file with specific formatting.

    Args:
        json_filename (str): The path to the input JSON file.
        csv_filename (str): The path to the output CSV file.
    """
    # read JSON data from file
    with open(json_filename, 'r') as json_file:
        data = json.load(json_file)

    # create CSV file
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # write header
        writer.writerow(['time', 'fees-usd-per-transaction'])

        # write rows
        for entry in data['fees-usd-per-transaction']:
            timestamp_ms = entry['x']  # time in milliseconds
            # convert to readable datetime format (DD.MM.YYYY)
            time_str = datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%d.%m.%Y')
            fee = entry['y']
            writer.writerow([time_str, fee])
def download_bitcoin_datasets():
    """
    Processes and downloads the required datasets using Selenium and performs necessary conversions.
    """
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": DOWNLOAD_DIRECTORY, "profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)

    try:
        print("Downloading the transaction count dataset..")
        driver.get(TRANSACTION_COUNT_DATASET_URL)
        download_button = driver.find_element(By.ID, TRANSACTION_COUNT_DATASET_BUTTON_ID)
        download_button.click()

        initial_time = time.time()
        while time.time() - initial_time < DOWNLOAD_TIMEOUT:
            files = os.listdir(DOWNLOAD_DIRECTORY)
            if TRANSACTION_COUNT_DATASET_DEFAULT_NAME in files:
                original_filename = os.path.join(DOWNLOAD_DIRECTORY, TRANSACTION_COUNT_DATASET_DEFAULT_NAME)
                custom_filename = os.path.join(DOWNLOAD_DIRECTORY, TRANSACTION_COUNT_DATASET_NEW_NAME)
                if os.path.exists(custom_filename):
                    os.remove(custom_filename)
                os.rename(original_filename, custom_filename)
                break
            time.sleep(1)

        print("Downloading the fees per transaction dataset..")
        driver.get(FEES_PER_TRANSACTION_DATASET_URL)
        all_button = WebDriverWait(driver, DOWNLOAD_TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, FEES_PER_TRANSACTION_DATASET_3Y_BUTTON_XPATH))
        )
        all_button.click()

        download_button = driver.find_element(By.CLASS_NAME, FEES_PER_TRANSACTION_DATASET_DOWNLOAD_BUTTON_CLASS_NAME)
        download_button.click()

        initial_time = time.time()
        while time.time() - initial_time < DOWNLOAD_TIMEOUT:
            files = os.listdir(DOWNLOAD_DIRECTORY)
            if FEES_PER_TRANSACTION_DATASET_DEFAULT_NAME in files:
                original_filename = os.path.join(DOWNLOAD_DIRECTORY, FEES_PER_TRANSACTION_DATASET_DEFAULT_NAME)
                custom_filename = os.path.join(DOWNLOAD_DIRECTORY, FEES_PER_TRANSACTION_DATASET_NEW_NAME)
                if os.path.exists(custom_filename):
                    os.remove(custom_filename)
                convert_json_to_csv(original_filename, custom_filename)
                os.remove(original_filename)
                break
            time.sleep(1)

        print("Downloading the bitcoin value dataset..")
        driver.get(BITCOIN_VALUE_DATASET_URL)

        initial_time = time.time()
        while time.time() - initial_time < DOWNLOAD_TIMEOUT:
            files = os.listdir(DOWNLOAD_DIRECTORY)
            if BITCOIN_VALUE_DATASET_DEFAULT_NAME in files:
                original_filename = os.path.join(DOWNLOAD_DIRECTORY, BITCOIN_VALUE_DATASET_DEFAULT_NAME)
                custom_filename = os.path.join(DOWNLOAD_DIRECTORY, BITCOIN_VALUE_DATASET_NEW_NAME)
                if os.path.exists(custom_filename):
                    os.remove(custom_filename)
                os.rename(original_filename, custom_filename)
                break
            time.sleep(1)

    finally:
        driver.quit()

def read_tsv_file(file_path):
    df = pd.read_csv(file_path, delimiter='\t')
    return df

# reformat from dd.mm.yyyy to yyyy-mm-dd
def reformat_date(date_str):
    dt = datetime.strptime(date_str, "%d.%m.%Y")
    formatted_date = dt.strftime("%Y-%m-%d")
    return formatted_date

# reformat from yyyy-mm-dd hh:mm:ss UTC to yyyy-mm-dd
def reformat_date2(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %Z")
    formatted_date = dt.strftime("%Y-%m-%d")
    return formatted_date

# reformat from yyyy_mm_dd to yyyy-mm-dd
def reformat_date3(date_str):
    dt = datetime.strptime(date_str, "%Y_%m_%d")
    formatted_date = dt.strftime("%Y-%m-%d")
    return formatted_date

def process_bitcoin_datasets(website_data_folder):

    file_path_transactions_per_day = os.path.join(website_data_folder, "aux_data", "transactions_per_day.tsv")
    file_path_price_market_per_day = os.path.join(website_data_folder, "aux_data", "price_market_per_day.csv")
    file_path_average_fee_per_day = os.path.join(website_data_folder, "aux_data", "fees_per_transaction.csv")
    
    # import and format the transactions per day dataset
    df_transactions_per_day = read_tsv_file(file_path_transactions_per_day)
    df_transactions_per_day['Time'] = df_transactions_per_day['Time'].apply(reformat_date)
    df_transactions_per_day.rename(columns={'sum(Transaction count – Blocks) – Bitcoin': 'transaction volume'}, inplace=True)
    df_transactions_per_day.rename(columns={'Time': 'date'}, inplace=True)

    # import and format the price_market per day dataset
    df_price_market_per_day = pd.read_csv(file_path_price_market_per_day)
    df_price_market_per_day = df_price_market_per_day[['snapped_at', 'price']]
    df_price_market_per_day['snapped_at'] = df_price_market_per_day['snapped_at'].apply(reformat_date2)
    df_price_market_per_day.rename(columns={'snapped_at': 'date'}, inplace=True)
    df_price_market_per_day.rename(columns={'price': 'market price'}, inplace=True)

    # import and format the average fees per day dataset
    df_average_fee_per_day = pd.read_csv(file_path_average_fee_per_day)
    df_average_fee_per_day['time'] = df_average_fee_per_day['time'].apply(reformat_date)
    df_average_fee_per_day.rename(columns={'time': 'date'}, inplace=True)
    df_average_fee_per_day.rename(columns={'fees-usd-per-transaction': 'average fee'}, inplace=True)
    aux = pd.merge(df_price_market_per_day, df_transactions_per_day, on='date', how='inner')
    return pd.merge(aux, df_average_fee_per_day, on='date', how='inner')

# get the paths of all statistical
def get_statistical_file_paths(start_directory):

    print("Start directory:")
    print(start_directory)
    print("end of start directory")

    # define the regex pattern for matching files ending with _stats.json
    regex = re.compile(r'.*_stats\.json')

    # initialize a list to store the matching file paths
    matching_files = []

    # walk through the directory tree

    for root, dirs, files in os.walk(start_directory):
        for file in files:
            # check if the file matches the regex
            if regex.match(file):
                # get the full path of the matching file
                full_path = os.path.join(root, file)

                # split the full path into parts
                path_parts = full_path.split(os.sep)
                
                # remove the first three parts
                new_path = os.sep.join(path_parts[3:])
                
                # append the modified path to the list
                matching_files.append(new_path)
    return matching_files

def create_statistical_dataset_name(input_path):
    # convert the input string into a Path object
    path = Path(input_path)
    
    # split the path into parts
    parts = list(path.parts)

    # initialize an empty list to store the converted parts
    converted_parts = []

    # iterate over the parts of the input path
    for index, part in enumerate(parts):
        if index == 0 and part == 'statistics':
            # if the first part is 'statistics', replace it with 'ln'
            converted_parts.append('ln')
        elif part == 'statistics':
            # skip any part that is 'statistics'
            continue
        elif part == 'graph_stats.json':
            converted_parts.append(part.replace('graph_stats.json', 'graph_stats'))
        elif part.endswith('_graph_stats.json'):
            # if the part ends with '_graph_stats.json', remove it
            converted_parts.append(part.replace('_graph_stats.json', ''))
        else:
            # otherwise, just add the part to the converted_parts list
            converted_parts.append(part)

    # join the parts with an underscore obtaining the name
    return '_'.join(converted_parts)


def create_statistical_dataset(input_path, dump_dates, data_folder, out_folder, bitcoin_dataset, website_data_folder):
    features = ['num_of_nodes', 'num_of_edges', 'average_degree', 'density', 'assortativity', 'average_clustering_coeff', 'num_of_triangles', 'giant_component_nodes']
    data = []
    # print("Inside create statistical dataset:")
    for date in dump_dates:
        path = os.path.join(out_folder, date, input_path)
        with open(path, 'r') as stats_file:
            json_data = json.loads(stats_file.read())
            json_data['giant_component_nodes'] = json_data['giant_component']['num_of_nodes']
            for k in list(json_data):
                if k not in features:
                    del json_data[k]
            
        
        # if the statistical file is about the statistics of the ln then import the network, compute the tot_capacity and add it as a column
        if input_path == os.path.join("statistics", "graph_stats.json"):
            with open(os.path.join(data_folder, f'network_graph_{date}.json'), 'r') as json_graph:
                graph_data = json.loads(json_graph.read())
                json_data['tot_capacity'] = sum([int(edge['capacity']) for edge in graph_data['edges']])
        
        json_data['date'] = reformat_date3(date)
        data.append(json_data)
    data = pd.DataFrame(data)
    
    if input_path == os.path.join("statistics", "graph_stats.json"):
        data['avg_capacity'] = data['tot_capacity'] / data['num_of_edges']
        data['average_degree'] = round(data['average_degree'], 3)
        data['avg_capacity'] = round(data['avg_capacity']/100_000_000, 4)
        data['tot_capacity'] = round(data['tot_capacity']/100_000_000, 4)

    dataset_name = create_statistical_dataset_name(input_path)

    # merge the datasets
    res = pd.merge(data, bitcoin_dataset, on='date', how='inner')
    res.to_csv(os.path.join(website_data_folder, f"{dataset_name}_dataset.csv"), index=False)

    # create the correlation matrix
    df_filtered = res.drop(columns=['date'])
    correlation_matrix = df_filtered.corr('spearman').round(5)

    # export the correlation matrix to a CSV file
    correlation_matrix.to_csv(os.path.join(f'{website_data_folder}', f'{dataset_name}_correlation_matrix.csv'))

def get_fraction_values(date, out_folder, diameter_dataset):
    path = os.path.join(f'{out_folder}', date, "attacks", diameter_dataset)
    df = pd.read_csv(path)
    return list(df['fraction_removed_nodes'])

def get_attacks_name(date, out_folder, diameter_dataset):
    path = os.path.join(f'{out_folder}', date, "attacks", diameter_dataset)
    df = pd.read_csv(path)
    return list(df.columns[1:])

# create the columns for an attack dataset
def create_columns(fraction_values):
    columns = []
    for target in ["diameter", "gc_size"]:
        for fraction_value in fraction_values:
            columns.append(target+"_with_fraction_"+str(fraction_value))
    return columns
    

def create_attack_dataset(dump_dates, out_folder, attack_name, in_datasets, bitcoin_dataset, website_data_folder):
    matrix = []

    # create the columns of the resulting dataset
    fraction_values = get_fraction_values(next(iter(dump_dates)), out_folder, in_datasets[0])
    fraction_columns = create_columns(fraction_values) + ['date']
    
    date_attack_folder = os.path.join(website_data_folder, 'attacks')
    print("Attack folder: "+ date_attack_folder)
    os.makedirs(date_attack_folder, exist_ok=True)
    
    # for each date build a row 
    for date in dump_dates:
        row = []
        
        for dataset in in_datasets:
            path = os.path.join(f'{out_folder}', date, "attacks", dataset)
            df = pd.read_csv(path)
            row += df[attack_name].tolist()
            # Save each imported file in the 'attacks/{date}' folder
            save_path = os.path.join(date_attack_folder, f'{date}_{dataset}')
            print("Attack folder: "+ save_path)
            df.to_csv(save_path, index=False)
        
        row += [reformat_date3(date)]
        matrix.append(row)
    aux = pd.DataFrame(matrix, columns=fraction_columns)


    # merge the datasets
    res = pd.merge(aux, bitcoin_dataset, on='date', how='inner')
    path = os.path.join(website_data_folder, f'attacks_{attack_name}_dataset.csv')
    res.to_csv(path, index=False)

    # create the correlation matrix
    res_filtered = res.drop(columns=['date'])

    correlation_matrix = res_filtered.corr().round(5)

    # export the correlation matrix to a CSV file
    path = os.path.join(website_data_folder, f'attacks_{attack_name}_correlation_matrix.csv')
    correlation_matrix.to_csv(path)


# create navigation bar structure
def create_navigation_bar_structure(website_data_path):
    website_datasets_paths = [x for x in listdir(website_data_path) if isfile(os.path.join(website_data_path, x))]
    
    # define the structure of the navigation bar 
    structure = [
        {
            "id": "ln",
            "sub-options": [],
            "label": "LN",
            "already-clicked": False
        },
        {
            "id": "attacks",
            "sub-options": [],
            "label": "Attacks",
            "already-clicked": False
        },
        {
            "id": "features",
            "sub-options": [],
            "label": "Sub-LN",
            "already-clicked": False
        },
        {
            "id": "synth",
            "sub-options": [],
            "label": "Synth-LN",
            "already-clicked": False
        },
        {
            "id": "comparison",
            "sub-options": [],
            "label": "Comparison",
            "already-clicked": False
        }
    ]

    # populate the 'sub-options' based on the filenames in 'website_datasets_paths'
    for path in website_datasets_paths:
        filename = os.path.basename(path) 

        # remove the '_correlation_matrix.csv' or '_dataset.csv' suffix
        base_name = filename.replace('_correlation_matrix.csv', '').replace('_dataset.csv', '')

        if "ln_" in base_name:
            option = base_name.split('ln_')[1]
            if option not in structure[0]["sub-options"]:
                structure[0]["sub-options"].append(option)
        elif "attacks_" in base_name:
            option = base_name.split('attacks_')[1]
            if option not in structure[1]["sub-options"]:
                structure[1]["sub-options"].append(option)
        elif "features_" in base_name:
            option = base_name.split('features_')[1].replace('_', ' ')
            if option not in structure[2]["sub-options"]:
                structure[2]["sub-options"].append(option)
        elif "synth_" in base_name:
            option = base_name.split('synth_')[1]
            if option not in structure[3]["sub-options"]:
                structure[3]["sub-options"].append(option)
        elif "comparison_" in base_name:
            option = base_name.split('comparison_')[1].replace('_', ' ')
            if option not in structure[4]["sub-options"]:
                structure[4]["sub-options"].append(option)

    nav_bar_structure_path = os.path.join(website_data_path, "aux_data", "nav_bar_structure.json")
    with open(nav_bar_structure_path, 'w') as json_file:
        json.dump(structure, json_file, indent=4)




if __name__ == '__main__':
    
    # check if you already have the bitcoin datasets
    download_bitcoin_datasets()
    print("Processing the bitcoin datasets..")
    bitcoin_dataset = process_bitcoin_datasets(WEBSITE_DATA_FOLDER)
    print(bitcoin_dataset)

    # get the dates from the filenames inside the datadir that match a specific pattern then remove all the duplicates, if any
    dump_dates = set(map(lambda x: x[:-5][14:], filter(lambda x: re.match(r'network_graph_\d{4}_\d{2}_\d{2}.json', x), os.listdir(DATA_FOLDER))))
    
    # create attack datasets
    print(f"Creating attack datasets and the relative correlation matrices for the website inside the folder {WEBSITE_DATA_FOLDER}..")
    for attack_name in get_attacks_name(next(iter(dump_dates)), OUTPUT_FOLDER, DIAMETER_DATASET):
        create_attack_dataset(sorted(list(dump_dates)), OUTPUT_FOLDER, attack_name, [DIAMETER_DATASET, GC_SIZE_DATESET], bitcoin_dataset, WEBSITE_DATA_FOLDER)

    # get the paths of the statistical files
    statistical_file_paths = get_statistical_file_paths(os.path.join(OUTPUT_FOLDER, next(iter(dump_dates))))
    # create statistical datasets
    print(f"Creating statistical datasets and the relative correlation matrices for the website inside the folder {WEBSITE_DATA_FOLDER}..")
    for path in statistical_file_paths:
        create_statistical_dataset(
            path, 
            sorted(list(dump_dates)), 
            data_folder=DATA_FOLDER, 
            out_folder=OUTPUT_FOLDER, 
            bitcoin_dataset=bitcoin_dataset,
            website_data_folder=WEBSITE_DATA_FOLDER
        )
    

    print("Creating navigation bar structure..")
    create_navigation_bar_structure(WEBSITE_DATA_FOLDER)
