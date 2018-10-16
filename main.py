import inspect
import math
import os
import random
import re
import string
import sys
import time
import hashlib

from datetime import datetime, timedelta
from pprint import pprint
from steem import Steem
from steem.blockchain import Blockchain
from steem.commit import Commit

debug = False

# Steem
steem_account      = os.environ['steem_account'] if 'steem_account' in os.environ else ''
steem_node         = os.environ['steem_node']

# Keys
steem_keys         = [
    os.environ['steem_wif'],
]
signing_keys       = [
    # list of keys for failover, including current key
]

# Connections - Steem
nodes = [steem_node]
s = Steem(nodes)

# globals
misses = 0
failover_after = 5
counter = 0;

# witness
witness_url = "https://yourwebsite.com"
witness_props = {
    "account_creation_fee": "3.000 STEEM",
    "maximum_block_size": 65536,
    "sbd_interest_rate": 0,
}

b = Blockchain(steemd_instance=s)
t = Commit(steemd_instance=s, no_broadcast=debug, keys=steem_keys)

def l(msg, slack=False):
    caller = inspect.stack()[1][3]
    print("[{}] {}".format(str(caller), str(msg)))
    sys.stdout.flush()

def get_witness_key():
    return s.get_witness_by_account(steem_account)['signing_key']

def get_misses():
    return s.get_witness_by_account(steem_account)['total_missed']

if __name__ == '__main__':
    l("Starting steemfailover", True)

    # get currently active key
    initial_key = get_witness_key()
    l("Initial Key: {}".format(initial_key))

    # determine initial misses
    initial_misses = get_misses()

    # removal current key
    signing_keys.remove(initial_key)

    # get the next key
    next_key = signing_keys.pop(0)

    disable_at = initial_misses + failover_after
    l("Initiated with {} misses, failover after {} more ({}).".format(initial_misses, failover_after, disable_at))
    while True:
        current_misses = get_misses()
        counter = (counter + 1) % 111
        if (counter == 0):
            l("Resetting initial misses to {}".format(current_misses))
            initial_misses = current_misses

        l("Currently {}, started at {}, stopping at {}".format(current_misses, initial_misses, disable_at))
        if current_misses >= disable_at:
            l("failover to {}".format(next_key))
            # Broadcast the next failover
            t.witness_update(signing_key=next_key, url=witness_url, props=witness_props, account=steem_account)
            # Do we have more keys?
            if len(signing_keys) > 0:
                # Move onto the next key and await more failures
                next_key = signing_keys.pop(0)
                disable_at = current_misses + failover_after
            else:
                # No more keys to failover to, script needs terminating
                l("terminating failover, no more keys to failover to!")
                quit(0)
        time.sleep(60)
