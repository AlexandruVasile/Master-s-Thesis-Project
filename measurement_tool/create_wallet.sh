#!/usr/bin/expect

set timeout -1

# Start wallet creation
spawn lncli --lnddir=/lnd_data create

# Expect wallet password prompt
expect "Input wallet password:"
send "NobodyWantsYourEmptyWallet00\r"

# Expect confirmation password prompt
expect "Confirm password:"
send "NobodyWantsYourEmptyWallet00\r"

# Expect mnemonic or extended master root key choice
expect {
    -re "Enter 'y' to use an existing cipher seed mnemonic, 'x' to use an extended master root key.*n" {
        send "n\r"
    }
}

# Handle the passphrase prompt for cipher seed encryption
expect "Input your passphrase if you wish to encrypt it (or press enter to proceed without a cipher seed passphrase):"
send "\r"  

# Wait for the process to complete
expect eof
