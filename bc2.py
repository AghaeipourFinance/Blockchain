## How run code in command line:
"""
curl http://127.0.0.1:5000/chain

curl -X POST -H "Content-Type: application/json" -d "{\"sender\":\"reza\",\"recipient\":\"mina\",\"amount\":15}" http://127.0.0.1:5000/trxs/new

"""

from datetime import datetime
import hashlib
import json
from flask import Flask , jsonify , request
import requests
from urllib.parse import urlparse
from uuid import uuid4

class Blackchain():
    def __init__(self):
        self.chain = []
        self.current_trxs = []
        self.nodes = set()
        self.create_block(proof=1, previous_hash='0')

    def create_block(self,proof,previous_hash = None):
        block = {'index':len(self.chain) + 1,
                 'timestamp':str(datetime.now()),
                 'proof':proof,
                 'trxs':self.current_trxs,
                 'previous_hash':previous_hash or hash(self.chain[-1])
                 }
        self.chain.append(block)
        return block
    
    def new_trx(self, sender ,recipient ,amount):
        self.current_trxs.append({'sender':sender , 'recipient':recipient ,
                                  'amount':amount})
        return self.last_block['index'] + 1 
    
    def register_node(self , address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    
    @staticmethod
    def hash(block):
        this_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(this_block).hexdigest()
    
    @property
    def last_block(self):
        return self.chain[-1]
    
    def proof_of_work(self , previous_proof):
        proof = 0
        valid_proof = False

        while valid_proof is False:
            my_hash = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if my_hash[:5] == '00000':
                valid_proof = True
            else:
                proof +=1
        return proof

    def vlid_chain(self , chain):
        previous_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            prev_proof = previous_block['proof']
            proof = block['proof']
            my_hash = hashlib.sha256(
                str(proof**2 - prev_proof**2).encode()).hexdigest()
            if my_hash[:5] != '00000':
                return False
        return True 
    
    def resolve_conflicts(self):
        new_chain = None
        max_length = len(self.chain) 
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chian']
                if length > max_length and self.vlid_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

app = Flask(__name__)

blockchain = Blackchain()
node_id = str(uuid4())

@app.route('/mine' , methods = ['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    # add reward
    blockchain.new_trx(sender='0' , recipient=node_id , amount=1)
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof , previous_hash)
    res = {'message':'new block created',
           'index':block['index'],
           'trxs':block['trxs'],
           'proof':block['proof'],
           'previous_hash':block['previous_hash']}
    return jsonify(res) , 200



@app.route('/trxs/new' , methods = ['POST'])
def new_trx():
    values = request.get_json()
    this_block = blockchain.new_trx(values['sender'] , values['sender'] , values['amount'])
    res = {'message':f'trx will be added to block {this_block}'}
    return jsonify(res) , 201

@app.route('/chain' , methods = ['GET'])
def display_chain():
    res = {'chain':blockchain.chain , 'length':len(blockchain.chain)}
    return jsonify(res) , 200

@app.route('/nodes/register',methods=['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')
    for node in nodes:
        blockchain.register_node(node)
    
    res = {'message':'new nodes have been added',
           'total_nodes':list(blockchain.nodes)}
    return jsonify(res) , 201


@app.route('/nodes/resolve',methods = ['GET'])
def consencus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        res = {'message':'our chain was replaced',
               'new_chain':blockchain.chain}
    else:
        res = {'message':'our chain is authoritative',
               'chain':blockchain.chain}
    return jsonify(res)        


if __name__ == '__main__':
    app.run(host='0.0.0.0' , port=5000)