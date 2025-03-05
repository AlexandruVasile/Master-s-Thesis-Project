# Master's Thesis Project


This is the repository related to the Master's Thesis "Longitudinal Measurements of the Bitcoin Lightning Network" 

This project aims to analyze the Bitcoin Lightning Network from multiple perspectives:

For the Longitudinal Graph Analysis:
- put in the folder "data" the downloaded snapshots from the following link: https://mega.nz/file/AmtCxZoD#-OwKZdsRjKeoZhBWo2-ADATFjFduFYVAX25KiFxjQdc
- ensure to have the requirements specified in requirements.txt 
- run "main.py"
  
The "main.py" and its related files were built by Ivan Gallo, https://github.com/ivxga/lightning_network_analysis

For running the website that shows the results of the Longitudinal Graph Analysis, correlated also with Bitcoin metrics:
- run "create_dataset_for_website.py" to create datasets for the website, based on your connection may require multiple attempts
- run "php -S 127.0.0.1:7777" to the website

For the Onchain Analysis:
- ensure you have a full bitcoin node running and synchronized
- run "bitcoin.py" inside "onchain" folder to collect Lightning Network data from the Blockchain
- run "get_statistical_properties.py" to run the Onchain analysis

Running your own data collection process:
- run the pruned Bitcoin node from the following link: https://mega.nz/file/I2kCWZTT#x2mtOjs7Wsb1fSM4v-W6_rmtruANUeaVy3swE49MAkA
- create a docker container from the Dockerfile inside the folder measurement_tool
- run it with:
docker run -it -v ./lnd:/lnd_data -v ./pruned_bitcoin_node/bitcoind:/bitcoind_data measurement_tool


In case you use the collected data, please cite the repository
