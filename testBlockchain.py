import sys
import time
import getpass
import json

from NodoBlockchain import NodoBlockchain
from Blockchain import Blockchain


nodo = NodoBlockchain("192.168.1.24", 50000, "Nodo 1")
nodo.start()

# nodo.connect_with_node("192.168.1.13", 50000)

time.sleep(1)
bc = Blockchain()

#crea due blocchi e li aggiunge alla blockchain
blocco1 = bc.crea_blocco("Gabriele Benedetti", "transazione1")
bc.aggiungi_blocco(blocco1)
time.sleep(1)
blocco2 = bc.crea_blocco("Francesco Pasquale", "transazione2")
bc.aggiungi_blocco(blocco2)
print('stampa registro:')
c = bc.db.cursor()
data = c.execute("SELECT * FROM blockchain").fetchall()
print(data)
# nodo.condividi_db("Nodo 2")

nodo.stop()
