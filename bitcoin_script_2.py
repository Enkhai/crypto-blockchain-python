from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.transactions import Sequence, TxInput, TxOutput, Transaction, Locktime
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

    # set a locking block height
    lock_block_height = 10

    # retrieve the private key of the original locking P2PKH address and the public key of the created P2SH address
    priv_key, p2sh_addr = create_p2sh(rpc_proxy, "/home/will/.bitcoin/regtest/wallets/mywallet",
                                      lock_block_height)
    # mine 100 blocks and send bitcoin to the P2SH address
    rpc_proxy.generatetoaddress(100, p2sh_addr)
    # mine 100 blocks to make mined bitcoin spendable, emulates 'bitcoin-cli -generate 100'
    for _ in range(100):
        rpc_proxy.generatetoaddress(1, rpc_proxy.getnewaddress())

    # retrieve unspent UTXOs for the P2SH address
    p2sh_addr_unspent = rpc_proxy.listunspent(0, 99999999, [p2sh_addr])

    # create absolute-block locking sequence for the transaction inputs
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, lock_block_height)

    # create transaction inputs for unspent UTXOs
    # and calculate the total unspent bitcoins they contain
    tx_inputs = []
    total_unspent = 0
    for utxo in p2sh_addr_unspent:
        # we have one transaction output (txout_index 0)
        tx_inputs.append(TxInput(utxo['txid'], 0, sequence=seq.for_input_sequence()))
        total_unspent += utxo['amount']
    print("Unspent bitcoin in address {} : {}".format(p2sh_addr, total_unspent))

    # create the address and keys for the funds to be sent to
    rec_pub_addr = rpc_proxy.getnewaddress()
    rec_priv_addr = rpc_proxy.dumpprivkey(rec_pub_addr)

    rec_sk = PrivateKey(rec_priv_addr)
    rec_pk = rec_sk.get_public_key()

    # calculate fee
    satoshis_per_kb = requests \
        .get('https://api.blockcypher.com/v1/btc/test3') \
        .json()['medium_fee_per_kb']
    # formula: |inputs| * 180 + 34 * |outputs| +- |inputs|
    tx_size = len(tx_inputs) * 180 + 34 * 1 + 10 + len(tx_inputs)
    # we calculate fees in terms of bitcoin
    fee = (tx_size / 1024) * (satoshis_per_kb / 10e8)

    # create the transaction output
    tx_output = TxOutput(to_satoshis(Decimal(total_unspent) - Decimal(fee)),
                         rec_pk.get_address().to_script_pub_key())
    # set a lock time in blocks for the transaction
    lock = Locktime(lock_block_height)
    # create the transaction
    tx = Transaction(tx_inputs, [tx_output], lock.for_transaction())
    unsigned_tx = tx.serialize()
    print('Raw unsigned transaction:', unsigned_tx)

    # we need to rebuild the redeem script from the P2SH private key
    # make the locking P2PKH address private key
    sender_sk = PrivateKey(priv_key)
    # retrieve the public key of the locking address
    sender_pk = sender_sk.get_public_key()
    # rebuild the redeem script
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP',
                            'OP_DUP', 'OP_HASH160', sender_pk.get_address().to_hash160(),
                            'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # for every input of the transaction
    for i, txin in enumerate(tx.inputs):
        # create the signature for redeeming the funds
        sig = sender_sk.sign_input(tx, i, redeem_script)
        # and sign the input
        txin.script_sig = Script([sig, sender_pk.to_hex(), redeem_script.to_hex()])

    signed_tx = tx.serialize()
    print('Raw signed transaction:', signed_tx)
    print('Transaction ID:', tx.get_txid())

    # verify that the transaction is valid
    ver = rpc_proxy.testmempoolaccept([signed_tx])
    if ver[0]['allowed']:
        # if the transaction is valid send the transaction to the blockchain
        print('Transaction is valid.')
        rpc_proxy.sendrawtransaction(signed_tx)
        print('{} Bitcoin sent to address {}'.format(Decimal(total_unspent) - Decimal(fee), rec_pub_addr))
    else:
        # otherwise, display the reason the transaction failed
        print('Transaction rejected. Reason:', ver[0]['reject-reason'])
