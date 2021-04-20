from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.transactions import Sequence
from bitcoinutils.constants import TYPE_RELATIVE_TIMELOCK
from bitcoinutils.keys import PrivateKey
from bitcoinutils.script import Script
from bitcoinutils.keys import P2shAddress
from bitcoinrpc.authproxy import JSONRPCException


def create_p2sh(proxy, wallet_file, blocks_to_lock, address_name=None):
    """
    Creates a P2SH address with a relative block locktime

        :param proxy: JSON RPC proxy for connecting to the network
        :param wallet_file: File containing the wallet
        :param blocks_to_lock: Number of future blocks the lock is valid for
        :param address_name: Name of the address locking the funds. If None, a new address will be created
        :return: tuple(address_privk, p2sh_addr): Tuple of private key of the locking address and key of the created P2SH address
    """

    # load wallet
    try:
        proxy.loadwallet(wallet_file)
    except JSONRPCException:
        # wallet already loaded
        pass

    # retrieve the public and private key strings of the specified address
    if address_name:
        address_pubk = list(proxy.getaddressesbylabel(address_name).keys())[0]
    else:
        address_pubk = proxy.getnewaddress()
    address_privk = proxy.dumpprivkey(address_pubk)

    # create the P2PKH key object
    p2pkh_sk = PrivateKey(address_privk)
    p2pkh_pk = p2pkh_sk.get_public_key().get_address()

    # create sequence for the redeem script
    seq = Sequence(TYPE_RELATIVE_TIMELOCK, blocks_to_lock)
    # create the redeem script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
                            'OP_DUP', 'OP_HASH160', p2pkh_pk.to_hash160(),
                            'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # create the P2SH address from the redeem script
    p2sh_addr = P2shAddress.from_script(redeem_script)
    # insert the P2SH address into the wallet
    proxy.importaddress(p2sh_addr.to_string())

    return address_privk, p2sh_addr.to_string()


if __name__ == '__main__':
    # set up the environment for regtest
    setup('regtest')
    username, password = "user", "pass"
    wallet = "/home/will/.bitcoin/regtest/wallets/mywallet"

    # set up a JSON RPC proxy
    rpc_proxy = NodeProxy(username, password).get_proxy()
    # retrieve the private key of the locking address and the key of the created P2SH address
    priv_key, p2sh_addr_key = create_p2sh(rpc_proxy, wallet, 10, "address1")

    # display the P2SH address key
    print("Created P2SH address key:", p2sh_addr_key)
