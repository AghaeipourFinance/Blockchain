import json
import hashlib
import sys
from time import time
from uuid import uuid4
import requests
from urllib.parse import urlparse
from flask import request, jsonify , Flask

class Blockchain():
    """new blockchain"""
    def __init__(self):
        self.chain = []
        self.current_trxs = []
        self.new_block(proof=100 , previous_hash=1)
        self.nodes = set()

    def new_block(self , proof ,previous_hash = None ):
        """create new block"""
        block = {'index': len(self.chain) + 1 ,
                 'timestamp': time(),
                 'trxs': self.current_trxs,
                 'proof':proof,
                 'previous_hash': previous_hash or self.hash(self.chain[-1])
                 }
        self.current_trxs = []
        self.chain.append(block)
        return block

    def new_trx(self, sender , recipient , amount):
        """add a new trx to the mempool"""
        self.current_trxs.append({'sender':sender , 'recipient':recipient , 'amount':amount})
        return self.last_block['index'] + 1
    
    def register_node(self , address):
        """add a new node to the blockchain"""
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def valid_chain(self, chain):
        """valid the blockchain"""
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'] , block['proof']):
                return False
            last_block = block
            current_index += 1
        return True
    
    def resolve_conflicts(self):
        """resolve conflicts"""
        neighbors = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain  = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    @staticmethod # it means hash only call in this function (dosent have self in its input)
    def hash(block):
        """hash a block"""
        block_string = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property # i can call lask_block as variable not a function
    def last_block(self):
        """get the last block in the chain"""
        return self.chain[-1]

    @staticmethod
    def valid_proof(last_proof , proof):
        """check if the proof is valid"""
        #TODO: it is better we hash whole block data instead of only last_proof
        this_proof = f'{proof}{last_proof}'.encode()
        this_proof_hash = hashlib.shake_256(this_proof).hexdigest(32)
        return this_proof_hash[:4] == '0000'

    def proof_of_work(self,last_proof):
        """show the work is done"""
        proof = 0
        while self.valid_proof(last_proof , proof) is False:
            proof += 1
        return proof


app = Flask(__name__)

node_id =  str(uuid4())
 
blockchain = Blockchain()

@app.route('/mine' , methods=['GET'])
def mine():
    """mine the blockchain"""
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    # reward the miner add to trxs
    blockchain.new_trx(sender='0' , recipient=node_id , amount=1)
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof , previous_hash)
    res = {'message':'new block created',
           'index':block['index'],
           'trxs':block['trxs'],
           'proof':block['proof'],
           'previous_hash':block['previous_hash']}
    return jsonify(res) , 200


@app.route('/trxs/new' , methods=['POST'])
def new_trx():
    """add a new trx to the mempool"""
    values = request.get_json()
    required = ['sender' ,'recipient' , 'amount' ]
    if not all(k in values for k in required):
        return "Missing values", 400
        
    this_block = blockchain.new_trx(values['sender'] , values['recipient'] , values['amount'])
    res = {'message':f'trx will be added to block {this_block}'}
    return jsonify(res) , 201

@app.route('/chain' , methods=['GET'])
def full_chain():
    """get the full chain"""
    res = {'chain':blockchain.chain , 'length':len(blockchain.chain)}
    return jsonify(res) , 200

@app.route('/nodes/register' , methods=['POST'])
def register_node():
    """register a new node"""
    values = request.get_json()
    nodes = values.get('nodes')
    for node in nodes: 
        blockchain.register_node(node)
    
    res = {'message':'new nodes have been added',
           'total_nodes':list(blockchain.nodes)}
    return jsonify(res) , 201

@app.route('/nodes/resolve' , methods=['GET'])
def consensus():
    """resolve conflicts"""
    replaced = blockchain.resolve_conflicts()
    if replaced:
        res = {'message':'our chain was replaced',
               'new_chain':blockchain.chain}
    else:
        res = {'message':'our chain is authoritative',
               'chain':blockchain.chain}
    return jsonify(res)


if __name__ == '__main__':
    app.run(host='0.0.0.0' , port=sys.argv[1])
