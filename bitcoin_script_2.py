from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.transactions import Sequence, TxInput, TxOutput, Transaction
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK
from bitcoinutils.keys import PrivateKey
from bitcoinutils.utils import to_satoshis
from bitcoinutils.script import Script
import requests
from decimal import Decimal

from bitcoin_script_1 import create_p2sh

if __name__ == '__main__':
    # set up the environment for regtest
    setup('regtest')
    username, password = "user", "pass"
    wallet = "/home/will/.bitcoin/regtest/wallets/mywallet"
    # set up a JSON RPC proxy
    rpc_proxy = NodeProxy(username, password).get_proxy()

    # retrieve the key of the created P2SH address
    _, p2sh_addr_key = create_p2sh(rpc_proxy, "/home/will/.bitcoin/regtest/wallets/mywallet",
                                   10)
    # mine 100 blocks and send bitcoin to the P2SH address
    rpc_proxy.generatetoaddress(100, p2sh_addr_key)
    # mine 100 blocks to make mined bitcoin spendable, emulates 'bitcoin-cli -generate'
    for _ in range(100):
        rpc_proxy.generatetoaddress(1, rpc_proxy.getnewaddress())

    # retrieve unspent UTXOs for the P2SH address
    p2sh_addr_unspent = rpc_proxy.listunspent(0, 99999999, [p2sh_addr_key])

    # create absolute-block locking sequence for the transaction inputs
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, 10)

    # create transaction inputs for unspent UTXOs
    # and calculate the total unspent bitcoins they contain
    tx_inputs = []
    total_unspent = 0
    for i in p2sh_addr_unspent:
        tx_inputs.append(TxInput(i['txid'], i['vout'], sequence=seq.for_input_sequence()))
        total_unspent += i['amount']
    print("Unspent bitcoin in address {} : {}".format(p2sh_addr_key, total_unspent))

    # create the address for the funds to be sent to
    p2pkh_pub_addr = rpc_proxy.getnewaddress()
    p2pkh_priv_addr = rpc_proxy.dumpprivkey(p2pkh_pub_addr)

    p2pkh_sk = PrivateKey(p2pkh_priv_addr)
    p2pkh_pk = p2pkh_sk.get_public_key()

    # calculate fee to ensure transaction confirmation within half an hour
    satoshis_per_kb = requests \
        .get('https://api.blockcypher.com/v1/btc/test3') \
        .json()['medium_fee_per_kb']
    tx_size = len(tx_inputs) * 180 + 34 * 1 + 10 + len(tx_inputs)
    fee = (tx_size / 1024) * satoshis_per_kb

    # create the transaction output
    tx_output = TxOutput(to_satoshis(Decimal(total_unspent) - Decimal(fee)),
                         p2pkh_pk.get_address().to_script_pub_key())
    # create the transaction
    tx = Transaction(tx_inputs, [tx_output])
    print('Raw unsigned transaction:', tx.serialize())

    # create the redeem script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
                            'OP_DUP', 'OP_HASH160', p2pkh_pk.to_hash160(),
                            'OP_EQUALVERIFY', 'OP_CHECKSIG'])
    # create the signature for redeeming the funds
    sig = p2pkh_sk.sign_input(tx, 0, redeem_script)
    # sign every input of the transaction
    for txin in tx.inputs:
        txin.script_sig = Script([sig, p2pkh_pk.to_hex(), redeem_script.to_hex()])

    print('Raw signed transaction:', tx.serialize())
    print('Transaction ID:', tx.get_txid())

    # verify that the transaction is valid
    ver = rpc_proxy.testmempoolaccept([tx.serialize()])
    if ver[0]['allowed']:
        # if the transaction is valid send the transaction to the blockchain
        print('Transaction is valid.')
        rpc_proxy.sendrawtransaction(tx.serialize())
        print('{} Bitcoin sent to address {}'.format(total_unspent - fee, p2pkh_pub_addr))
    else:
        print('Transaction rejected. Reason:', ver[0]['reject-reason'])
