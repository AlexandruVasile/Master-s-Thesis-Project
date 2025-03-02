#!/usr/bin/expect -f

# while true; do
#     lncli --lnddir=lnd_data state
#     echo $?
# done

# set timeout -1

spawn lncli --lnddir=/lnd_data unlock
 
expect "Input wallet password:"
 
send -- "NobodyWantsYourEmptyWallet00\r"

# expect "[lncli] rpc error: code = Unknown desc = wallet not found"

# spawn lncli --lnddir=/lnd_data create

# expect "Input wallet password:\r"

# send -- "NobodyWantsYourEmptyWallet00\r"

# expect "Confirm password:\r"

# send -- "NobodyWantsYourEmptyWallet00\r"

# expect "Enter 'y' to use an existing cipher seed mnemonic, 'x' to use an extended master root key or 'n' to create a new seed (Enter y/x/n):"

# send -- "n\r"

# # Handle the passphrase prompt for the cipher seed
# expect "Input your passphrase if you wish to encrypt it (or press enter to proceed without a cipher seed passphrase):"
# send -- "\r"  # Just press Enter

expect eof


