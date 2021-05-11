import sys

from bitcoinrpc.authproxy import JSONRPCException
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK
from bitcoinutils.keys import P2shAddress
from bitcoinutils.keys import PublicKey
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Sequence


def create_p2sh(proxy, block_height=10, address_pubk=None):
    """
    Creates a P2SH address with an absolute block locktime.

        :param proxy: JSON RPC proxy for connecting to the network.
        :param block_height: Block height the lock is valid for. Default value is 10.
        :param address_pubk: Public key of the address locking the funds. If None, a new address will be created.
    """

    # if a public key is not specified, create a new address and display its keys for future use
    if not address_pubk:
        print('Public key not provided. Created a new address.')
        address = proxy.getnewaddress()
        print('Address:', address)
        address_privk = proxy.dumpprivkey(address)
        print('Private key:', address_privk)
        address_pubk = proxy.getaddressinfo(address)['pubkey']
        print('Public key:', address_pubk)
    # create the public key object
    p2pkh_pk = PublicKey(address_pubk)

    # create sequence for the redeem script
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, block_height)
    # create the redeem script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
                            'OP_DUP', 'OP_HASH160', p2pkh_pk.to_hash160(),
                            'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # create the P2SH address from the redeem script
    p2sh_addr = P2shAddress.from_script(redeem_script)
    # insert the P2SH address into the wallet
    proxy.importaddress(p2sh_addr.to_string())

    # display the P2SH address
    print('Created P2SH address:', p2sh_addr.to_string())


if __name__ == '__main__':
    # default arguments
    height = 10
    pubk = None

    # retrieve the arguments
    try:
        height = int(sys.argv[1])
        pubk = sys.argv[2]
    except IndexError:
        # ignore missing arguments
        pass

    # set up the environment for regtest
    setup('regtest')
    username, password = 'user', 'pass'
    wallet = '~/.bitcoin/regtest/wallets/mywallet'
    # set up a JSON RPC proxy
    rpc_proxy = NodeProxy(username, password).get_proxy()

    # load wallet
    try:
        rpc_proxy.loadwallet(wallet)
    except JSONRPCException:
        # wallet already loaded
        pass

    # run the script
    create_p2sh(rpc_proxy, height, pubk)
