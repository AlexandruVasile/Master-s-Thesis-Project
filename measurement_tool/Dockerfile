# use the lightninglabs Bitcoin Core image as the base
FROM lightninglabs/bitcoin-core:${BITCOIN_VERSION:-25}

# set environment variables for Go
ENV GO_VERSION=1.20.4
ENV GOPATH=/mnt/data/go_env
ENV PATH=$PATH:$GOPATH/bin

# install required packages including Go and expect
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    git \
    build-essential \
    jq \
    bc \
    python3 \
    expect \
    && rm -rf /var/lib/apt/lists/*

# install Go
RUN wget https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# create Go environment directory
RUN mkdir -p $GOPATH

# set up the Go environment variables in .bashrc
RUN echo "export GOPATH=$GOPATH" >> /root/.bashrc && \
    echo "export PATH=\$PATH:\$GOPATH/bin" >> /root/.bashrc

# copy necessary binaries into the /bin directory in the container
COPY bitcoin_bin /bin/
COPY lnd_bin /mnt/data/go_env/bin/

# copy the start.sh script to the root directory of the container
COPY start.sh /start.sh
COPY unlock.sh /unlock.sh
COPY create_wallet.sh /create_wallet.sh
COPY compress_snapshot.py /compress_snapshot.py

# set execute permissions for the scripts
RUN chmod +x /start.sh
RUN chmod +x /unlock.sh
RUN chmod +x /create_wallet.sh
RUN chmod +x /compress_snapshot.py

# set start.sh as the default command to run when the container starts
CMD ["/start.sh"]
