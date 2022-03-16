import json
import hashlib
import sqlite3
from datetime import time, date, datetime

from base64 import b64decode, b64encode

from Nodo import Nodo


class Blockchain:
    """Questa classe implementa la funzionalità di una blockchain immutabile. Si può conservare qualsiasi cosa nella
    struttura dati blockchain ma non si può cancellare nulla dopo averlo inserito (salvo cancellare il database).
    Una blockchain è un registro che crea e modifica i record dello stato degli oggetti. Prima di poter aggiungere un record,
    questo deve essere prima verificato."""

    def __init__(self):
        super(Blockchain, self).__init__()

        # Il database che contiene la blockchain.
        self.db = sqlite3.connect('blockchain.db', check_same_thread = False)
        self.init_database()
        
    def init_database(self):
        c = self.db.cursor()
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='blockchain'")
        if ( c.fetchone()[0] != 1 ):
            c.execute("""CREATE TABLE blockchain(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       prev_hash TEXT,
                       type TEXT,
                       timestamp TEXT,
                       data TEXT,
                       nonce TEXT, 
                       hash TEXT)""")

    def check_blocco(self, blocco):
        return True
            
    def aggiungi_blocco(self, blocco):
        """Questo metodo aggiunge un nuovo blocco alla blockchain. 
           Controlla che gli hash del blocco e del blocco precedente siano corretti prima che venga aggiunto."""
        if ( self.check_blocco(blocco) ):
            c = self.db.cursor()
            c.execute("INSERT INTO blockchain (prev_hash, type, timestamp, data, nonce, hash) VALUES (?, ?, ?, ?, ?, ?)",
                      ( blocco["prev_hash"],
                        blocco["type"], 
                        blocco["timestamp"],
                        json.dumps(blocco["data"], sort_keys=True),
                        blocco["nonce"],
                        blocco["hash"] ))
            self.db.commit()
            return True

        return False

    def restituisci_record_blockchain(self, data):
        header = ("id", "prev_hash", "type", "timestamp", "data", "nonce", "hash")
        
        if ( len(data) != len(header) ):
            print("La Blockchain non contiene i " + len(header) + " elementi richiesti")
            return None

        record = {}
        for i in range(len(header)):
            record[header[i]] = data[i]
            
        return record
        
    def restituisci_blocco(self, index):
        # Questo metodo restituisce il blocco dell'indice dato. Quando l'indice non esiste, viene restituito None.
        c = self.db.cursor()
        c.execute("SELECT * FROM blockchain WHERE id=?", (index,))

        data = c.fetchone()
        if ( data != None ):
            return self.restituisci_record_blockchain(data)

        return None
            
    def restituisci_ultimo_blocco(self):
        # Questo metodo restituisce l'ultimo blocco della blockchain.
        c = self.db.cursor()
        for row in c.execute('SELECT * FROM blockchain ORDER BY id DESC LIMIT 1'):
            return self.restituisci_record_blockchain(row)
        return None

    def crea_blocco(self, data, type):
        """Questo metodo crea un nuovo blocco da inserire nella blockchain. 
           Utilizza la proof-of-work per rendere la blockchain immutabile e non hackerabile. 
           Per migliorare la catena, i blocchi devono essere aggiunti costantemente."""
        ultimo_blocco = self.restituisci_ultimo_blocco()
        print("LAST:")
        print(ultimo_blocco)
        timestamp = datetime.now()
        blocco = {
            "id"       : (ultimo_blocco["id"] + 1) if ultimo_blocco != None else 1,
            "prev_hash": ultimo_blocco["hash"] if ultimo_blocco != None else 0,
            "type"     : type,
            "timestamp": timestamp.isoformat(),
            "data"     : data,
            "nonce"    : 0
        }

        # Implementazione della proof-of-work
        difficoltà = 5
        h = hashlib.sha512()
        h.update( json.dumps(blocco, sort_keys=True).encode("utf-8") )
        while ( h.hexdigest()[:difficoltà] != "0"*difficoltà ):
            blocco["nonce"] = blocco["nonce"] + 1
            h.update( json.dumps(blocco, sort_keys=True).encode("utf-8") )

        blocco["hash"] = h.hexdigest()

        return blocco


