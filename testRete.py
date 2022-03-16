import sys 
import time

from Nodo import Nodo


nodo = Nodo("192.168.1.24", 50000, "Nodo 1")
nodo.start()


nodo.connect_with_node("192.168.1.37", 50000)

time.sleep(2)

print('invio messaggio 1')
nodo.send_to_nodes('Nodo 1 invia messaggio 1')

time.sleep(5)

print('invio messaggio 3')
nodo.send_to_nodes('Nodo 1 invia messaggio 3')

time.sleep(2)

nodo.stop()
time.sleep(1)
