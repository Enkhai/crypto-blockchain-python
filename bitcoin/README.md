# Bitcoin scripting examples

Bitcoin scripting examples using the Python [bitcoin-utils library](https://github.com/karask/python-bitcoin-utils)

## Prerequisites

- Bitcoin Core
    - [Linux installation instructions](https://bitcoin.org/en/full-node#linux-instructions)
    - [Windows installation instructions](https://bitcoin.org/en/full-node#windows-instructions)
- Python 3.6 +
    - Anaconda distribution
        - [Linux installation guide](https://docs.anaconda.com/anaconda/install/linux/)
        - [Windows installation guide](https://docs.anaconda.com/anaconda/install/windows/)
    - Python
        - [Linux installation guide](https://realpython.com/installing-python/#how-to-install-python-on-linux)
        - [Windows installation guide](https://realpython.com/installing-python/#how-to-install-python-on-windows)

## Installing libraries

- Create a new Python environment and activate it.
- Install needed libraries by running `pip install -r /path/to/requirements.txt`.
- The environment should be ready to go.

## Bitcoin setup

You should edit your bitcoin.conf files by setting the following values:

```
regtest=1
server=1
rpcuser=user
rpcpassword=pass
```

By default, bitcoin.conf is located in `~/.bitcoin` in Linux, and in `C:\Users\<user>\AppData\Roaming\Bitcoin` in
Windows. If the file does not exist in those locations, create it using the values presented above.

Next up, you should start the bitcoin daemon. Since we set up `regtest=1`, the daemon should start in regtest mode,
which is your local Bitcoin debugging environment.

To start the daemon, run `bitcoind` in a new terminal in Linux, or `C:\Program Files\Bitcoin\daemon\bitcoind` in
Windows.

As a final step, you should create a new wallet named `mywallet`. To do that, run `bitcoin-cli createwallet mywallet` in
Linux, or `C:\Program Files\Bitcoin\daemon\bitcoin-cli createwallet mywallet` in Windows.

## Script descriptions

### Script 1

Script 1 creates a P2SH address with an absolute locktime, given a public P2PKH key.<br>
The script receives 2 arguments, a block height for the locktime and the public key, in that specific order.<br>
One can skip either one or both of the arguments. If the public key argument is skipped, a new address is created and
the address, along with the private and public keys, is displayed.<br>
If the block height is also skipped, a default value of height 10 is used instead.<br>
At the end, the P2SH address is inserted into your wallet and displayed.

### Script 2

Script 2 spends funds from a P2SH address with an absolute locktime to a receiving address.<br>
To achieve that, the script receives 4 arguments; the block height of the locktime, the private key of the P2PKH address
locking the funds, the P2SH address, and the P2PKH receiving address.<br>
To ensure funds exist in the P2SH address, the script generates 100 blocks to that address and ensures they become
spendable by generating another 100 blocks.<br>
Afterwards, the total amount of bitcoin in the P2SH address, and the necessary fees for the transaction are calculated,
and a transaction for sending the funds is constructed, signed, and finally, sent to the blockchain.<br>
At the end, if the transaction is successful, an appropriate message will be displayed.<br>
Otherwise, if there is an error, you should make sure you have specified your arguments correctly.

## Running the scripts

__Scripts should be run one after the other.__

### Script 1

To run the first script, you should specify a block height, and optionally, an address public key.<br>
If a public key is not specified, the script will create a new address and display its value, public key, and private
key.

Alternately, you should create a new address by running `bitcoin-cli getnewaddress`.<br>
Keep the address value and then run `bitcoin-cli dumpprivkey <address>`. This is your address private key. You will need
the private key for the second script.<br>
Next, run `bitcoin-cli getaddressinfo <address>` and keep your `pubkey`. This is the public key you will use to run the
fist script.

The command for running the first script should look something like this:

- No arguments - the script will generate a new address, displaying the public and private key, and the P2SH address
  with a default block height of 10<br>
  `python /path/to/scripts/bitcoin_script1.py`
- Using only block height - the script will generate a new address and display the public and private key<br>
  `python /path/to/scripts/bitcoin_script1.py <block height>`
- Complete example<br>
  `python /path/to/scripts/bitcoin_script1.py <block height> <public key>`

### Script 2

After you are done with the first script, you should have noted down

- the block height
- the private key of the P2PKH address locking the funds
- and the P2SH address

As a bonus, you will also need a receiving P2PKH address to send the funds to.<br>
To do that, simply run `bitcoin-cli getnewaddress` and note down the address.

The command for running the second script should look something like this:<br>
`python /path/to/scripts/bitcoin_script2.py <block height> <private key> <P2SH address> <receiver address>`
