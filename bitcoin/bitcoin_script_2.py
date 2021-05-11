import sys
from decimal import Decimal

import requests
from bitcoinrpc.authproxy import JSONRPCException
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK
from bitcoinutils.keys import PrivateKey, PublicKey
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.script import Script
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Sequence, TxInput, TxOutput, Transaction, Locktime
from bitcoinutils.utils import to_satoshis


def spend_p2sh_cltv_p2pkh(proxy, block_height, sender_priv_key, p2sh_addr, rec_addr):
    """
    Spends funds from a P2SH address with an absolute locktime to a P2PKH receiver address.
    :param proxy: JSON RPC proxy for connecting to the network.
    :param block_height: Block height the lock is valid for.
    :param sender_priv_key: Private key of the address locking the funds.
    :param p2sh_addr: P2SH address containing the funds.
    :param rec_addr: P2PKH address receiving the funds.
    """

    # mine 100 blocks and send bitcoin to the P2SH address
    proxy.generatetoaddress(100, p2sh_addr)
    # mine 100 blocks to make mined bitcoin spendable, emulates 'bitcoin-cli -generate 100'
    for _ in range(100):
        proxy.generatetoaddress(1, proxy.getnewaddress())

    # retrieve unspent UTXOs for the P2SH address
    p2sh_addr_unspent = proxy.listunspent(0, 99999999, [p2sh_addr])

    # create absolute-block locking sequence for the transaction inputs
    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, block_height)

    # create transaction inputs for unspent UTXOs
    # and calculate the total unspent bitcoins they contain
    tx_inputs = []
    total_unspent = 0
    for utxo in p2sh_addr_unspent:
        tx_inputs.append(TxInput(utxo['txid'], utxo['vout'], sequence=seq.for_input_sequence()))
        total_unspent += utxo['amount']
    print("Unspent bitcoin in address {} : {}".format(p2sh_addr, total_unspent))

    # get the public key of the receiving address for the funds to be sent to
    rec_pub_key = proxy.getaddressinfo(rec_addr)['pubkey']
    rec_pk = PublicKey(rec_pub_key)

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
    lock = Locktime(block_height)
    # create the transaction
    tx = Transaction(tx_inputs, [tx_output], lock.for_transaction())
    unsigned_tx = tx.serialize()
    print('Raw unsigned transaction:', unsigned_tx)

    # we need to rebuild the redeem script from the P2SH private key
    # make the locking P2PKH address private key
    sender_sk = PrivateKey(sender_priv_key)
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
    ver = proxy.testmempoolaccept([signed_tx])
    if ver[0]['allowed']:
        # if the transaction is valid send the transaction to the blockchain
        print('Transaction is valid.')
        proxy.sendrawtransaction(signed_tx)
        print('{} Bitcoin sent to address {}'.format(Decimal(total_unspent) - Decimal(fee), rec_addr))
    else:
        # otherwise, display the reason the transaction failed
        print('Transaction rejected. Reason:', ver[0]['reject-reason'])


if __name__ == '__main__':
    # retrieve the arguments
    height = int(sys.argv[1])
    privk = sys.argv[2]
    p2sh = sys.argv[3]
    receiver = sys.argv[4]

    # set up the environment for regtest
    setup('regtest')
    username, password = "user", "pass"
    wallet = "~/.bitcoin/regtest/wallets/mywallet"
    # set up a JSON RPC proxy
    rpc_proxy = NodeProxy(username, password).get_proxy()

    # load wallet
    try:
        rpc_proxy.loadwallet(wallet)
    except JSONRPCException:
        # wallet already loaded
        pass

    spend_p2sh_cltv_p2pkh(rpc_proxy, height, privk, p2sh, receiver)
