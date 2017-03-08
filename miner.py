import urllib2
import json
import argon2
import time
from struct import pack, unpack
import random
import requests

NODE_URL = "http://6857coin.csail.mit.edu:8080"

"""
    This is a bare-bones miner compatible with 857coin, minus the final proof of
    work check. We have left lots of opportunities for optimization. Partial
    credit will be awarded for successfully mining any block that appends to
    a tree rooted at the genesis block. Full credit will be awarded for mining
    a block that adds to the main chan. Note that the faster you solve the proof
    of work, the better your chances are of landing in the main chain.

    Feel free to modify this code in any way, or reimplement it in a different
    language or on specialized hardware.

    Good luck!
"""

def solve_block(b):
    """
    Iterate over random nonces until a valid proof of work is found
    for the block

    Expects a block dictionary `b` with difficulty, version, parentid,
    timestamp, and root (a hash of the block data).

    """
    d = b["difficulty"]
    b["nonce"] = rand_nonce(b["difficulty"])
    while True:
        b["nonce"] += 1
        h = hash_block_to_hex(b)
        # TODO: verify PoW

def main():
    """
    Repeatedly request next block parameters from the server, then solve a block
    containing our team name.

    We will construct a block dictionary and pass this around to solving and
    submission functions.
    """
    block_contents = "cc"
    while True:
        #   Next block's parent, version, difficulty
        next_header = get_next()
        #   Construct a block with our name in the contents that appends to the
        #   head of the main chain
        new_block = make_block(next_header, block_contents)
        #   Solve the POW
        print "Solving block..."
        print new_block
        solve_block(new_block)
        #   Send to the server
        add_block(new_block, block_contents)

def get_next():
    """
       Parse JSON of the next block info
           difficulty      uint64
           parentid        HexString
           version         single byte
    """
    return json.loads(urllib2.urlopen(NODE_URL + "/next").read())

def add_block(h, contents):
    """
       Send JSON of solved block to server.
       Note that the header and block contents are separated.
            header:
                difficulty      uint64
                parentid        HexString
                root            HexString
                timestampe      uint64
                version         single byte
            block:          string
    """
    add_block_request = {"header": h, "block": contents}
    print "Sending block to server..."
    print json.dumps(add_block_request)
    r = requests.post(NODE_URL + "/add", data=json.dumps(add_block_request))
    print r

def hash_block_to_hex(b):
    """
    Computes the hex-encoded hash of a block header. First builds an array of
    bytes with the correct endianness and length for each arguments. Then hashes
    the concatenation of these bytes and encodes to hexidecimal.
    """
    packed_data = []
    packed_data.extend(b["parentid"].decode('hex'))
    packed_data.extend(b["root"].decode('hex'))
    packed_data.extend(pack('>Q', long(b["difficulty"])))
    packed_data.extend(pack('>Q', long(b["timestamp"])))
    packed_data.extend(pack('>Q', long(b["nonce"])))
    packed_data.append(chr(b["version"]))
    if len(packed_data) != 89:
	    print "invalid length of packed data"
    b["hash"] = hash_to_hex(''.join(packed_data))
    return b["hash"]

def hash_to_hex(data):
    """Returns the hex-encoded hash of a byte string."""
    raw = argon2.low_level.hash_secret_raw(
      data, b'somesalt',
      3, 1 << 12, 1, 32, argon2.low_level.Type.D
    )
    return ''.join('{:02x}'.format(ord(c)) for c in raw)

def make_block(next_info, contents):
    """
    Constructs a block from /next header information `next_info` and sepcified
    contents.
    """
    block = {
        "version": next_info["version"],
        #   for now, root is hash of block contents (team name)
        "root": hash_to_hex(contents),
        "parentid": next_info["parentid"],
        #   nanoseconds since unix epoch
        "timestamp": long(time.time()*1000*1000*1000),
        "difficulty": next_info["difficulty"]
    }
    return block

def rand_nonce(diff):
    """
    Returns a random int in [0, 2**diff)
    """
    return random.randint(0,2**diff-1)

if __name__ == "__main__":
    main()
