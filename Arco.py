import socket
import time
import threading
import json


class Connessione(threading.Thread):
    """La classe "Connessione" è utilizzata dalla classe "Nodo" e rappresenta la connessione socket TCP/IP con un altro nodo.
       Questa classe si occupa della connessione dei nodi sia in entrata che in uscita e della comunicazione tra loro. 
       La classe contiene il socket client e contiene le informazioni sull'id del nodo di connessione.
       Crea un'istanza di una nuova connessione."""


    def __init__(self, main_node, sock, id, host, porta):
        """Istanzia una nuova "Connessione". Tutta la comunicazione TCP/IP è gestita da questa classe.
            main_node: La classe Nodo che ha ricevuto la connessione.
            sock: Il socket associato alla connessione del client.
            id: L'id del nodo connesso (sul lato opposto della connessione TCP/IP).
            host: L'host/ip del nodo principale (main).
            porta: La porta del nodo principale (main)."""

        super(Connessione, self).__init__()

        self.host = host
        self.porta = porta
        self.main_node = main_node
        self.sock = sock
        self.terminate_flag = threading.Event()

        # l'id del nodo connesso
        self.id = str(id) 

        # Carattere di fine trasmissione per i messaggi in streaming di rete.
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')

        # Datastore per memorizzare informazioni aggiuntive relative al nodo.
        self.info = {}

        # Uso il timeout del socket per determinare i problemi con la connessione
        self.sock.settimeout(10.0)

        self.main_node.debug_print("Connessione.send: Inizio con client (" + self.id + ") '" + self.host + ":" + str(self.porta) + "'")

    def send(self, data, encoding_type='utf-8'):
        """Invia i dati al nodo connesso. I dati possono essere di puro testo (str), oggetto dizionario (json) e oggetto bytes.
           Quando si invia l'oggetto byte, si utilizza la comunicazione socket standard. Un carattere di fine trasmissione 0x04
           utf-8/ascii sarà usato per decodificare i pacchetti ricevuti dall'altro nodo. Quando il socket è danneggiato, la connessione del nodo
           viene interrotta."""
        if isinstance(data, str):
            try:
                self.sock.sendall( data.encode(encoding_type) + self.EOT_CHAR )

            except Exception as e: # Quando l'invio non riesce chiude la connessione
                self.main_node.debug_print("Connessione.send: Errore nell'invio dei dati al nodo: " + str(e))
                self.stop() # Termina il nodo

        elif isinstance(data, dict):
            try:
                json_data = json.dumps(data)
                json_data = json_data.encode(encoding_type) + self.EOT_CHAR
                self.sock.sendall(json_data)
                
            except TypeError as type_error:
                self.main_node.debug_print('Dict non valido')
                self.main_node.debug_print(str(type_error))

            except Exception as e: # Quando l'invio non riesce chiude la connessione
                self.main_node.debug_print("Connessione.send: Errore nell'invio dei dati al nodo: " + str(e))
                self.stop() 

        elif isinstance(data, bytes):
            bin_data = data + self.EOT_CHAR
            self.sock.sendall(bin_data)

        else:
            self.main_node.debug_print('datatype non valido, usare str, dict (sarà inviato come json) o bytes')


    def stop(self):
        # Termina la connessione e il thread viene interrotto.
        self.terminate_flag.set()

    def parse_packet(self, packet):
        """Analizza il pacchetto e determina se è stato inviato in formato str, json o byte. Restituisce
           i dati corrispondenti."""
        try:
            packet_decoded = packet.decode('utf-8')

            try:
                return json.loads(packet_decoded)

            except json.decoder.JSONDecodeError:
                return packet_decoded

        except UnicodeDecodeError:
            return packet

    def run(self):
        """Il ciclo principale del thread per gestire la connessione con il nodo. 
           All'interno del ciclo principale il thread attende di ricevere i dati dal nodo. 
           Se i dati vengono ricevuti, verrà invocato il metodo node_message del nodo principale."""  
           
        buffer = b'' # Controlla il flusso in entrata

        while not self.terminate_flag.is_set():
            chunk = b''

            try:
                chunk = self.sock.recv(4096) 

            except socket.timeout:
                self.main_node.debug_print("Connessione: timeout")

            except Exception as e:
                self.terminate_flag.set() # Problema nel terminare la connessione
                self.main_node.debug_print('Errore')
                self.main_node.debug_print(str(e))

            # Possibile overflow del buffer quando non viene trovato EOT_CHAR 
            if chunk != b'':
                buffer += chunk
                eot_pos = buffer.find(self.EOT_CHAR)

                while eot_pos > 0:
                    packet = buffer[:eot_pos]
                    buffer = buffer[eot_pos + 1:]

                    self.main_node.message_count_ricevuti += 1
                    self.main_node.node_message( self, self.parse_packet(packet) )

                    eot_pos = buffer.find(self.EOT_CHAR)

            time.sleep(1)

        self.sock.settimeout(None)
        self.sock.close()
        self.main_node.node_disconnected( self ) 
        self.main_node.debug_print("Connessione: Interrotta")

    def set_info(self, key, value):
        self.info[key] = value

    def get_info(self, key):
        return self.info[key]

    def __str__(self):
        return 'Connessione: {}:{} <-> {}:{} ({})'.format(self.main_node.host, self.main_node.porta, self.host, self.porta, self.id)

    def __repr__(self):
        return '<Connessione: Nodo {}:{} <-> Connessione {}:{}>'.format(self.main_node.host, self.main_node.porta, self.host, self.porta)
