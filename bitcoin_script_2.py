from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy

from bitcoin_script_1 import create_p2sh

if __name__ == '__main__':

    # set up the environment for regtest
    setup('regtest')
    username, password = "user", "pass"
    wallet = "/home/will/.bitcoin/regtest/wallets/mywallet"
    # set up a JSON RPC proxy
    rpc_proxy = NodeProxy(username, password).get_proxy()

    # retrieve the private key of the locking address and the key of the created P2SH address
    p2pkh_addr_priv_key, p2sh_addr_key = create_p2sh(rpc_proxy, "/home/will/.bitcoin/regtest/wallets/mywallet",
                                   "address1", 10)

