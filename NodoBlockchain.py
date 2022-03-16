import time
import json
import hashlib
import sqlite3
from base64 import b64decode, b64encode

from Nodo import Nodo
from Blockchain import Blockchain


class NodoBlockchain(Nodo):
    """description of class"""
    def __init__(self, host, porta, id = None):

        super(NodoBlockchain, self).__init__(host, porta, id)

        self.blockchain = Blockchain()

    def node_message(self, node, data): 
    
        c = self.blockchain.db.cursor()
        elem = c.execute("SELECT * FROM blockchain").fetchall()
        if (len(elem)!= 0):
            for row in elem:
                if (data[0] == row[0]):
                    print("blocco già presente nel database")
                    return None
                else:
                    c.execute("INSERT INTO blockchain (id, prev_hash, type, timestamp, data, nonce, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ( data[0],
                        data[1],
                        data[2], 
                        data[3],
                        data[4],
                        data[5],
                        data[6] ))
        else:
            c.execute("INSERT INTO blockchain (id, prev_hash, type, timestamp, data, nonce, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      ( data[0],
                        data[1],
                        data[2], 
                        data[3],
                        data[4],
                        data[5],
                        data[6] ))
        self.blockchain.db.commit()
    
    def condividi_db(self, id):

        c = self.blockchain.db.cursor()
        data = c.execute("SELECT * FROM blockchain").fetchall()
        for n in self.nodes_inbound:
            if n.id == id:
                for row in data:
                    self.send_to_node(n, json.dumps(row))
        for n in self.nodes_outbound:
            if n.id == id:
                for row in data:
                    self.send_to_node(n, json.dumps(row))

                   
        
       


    


