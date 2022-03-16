import socket
import time
import threading
import random
import hashlib

from Arco import Connessione

class Nodo(threading.Thread):

    def __init__(self, host, porta, id = None):

        super(Nodo, self).__init__()

        self.terminate_flag = threading.Event()

        self.host = host
        self.porta = porta


        self.nodes_inbound = []  # nodi connessi con me
        self.nodes_outbound = []  # nodi a cui sono connesso

        # Lista di nodi a cui bisogna riconnettersi in caso di connessione persa
        self.reconnect_to_nodes = []

        # Crea un ID per ogni nodo qualora non ne esista uno
        if id == None:
            self.id = self.generate_id()

        else:
            self.id = str(id)

        # Avvia il server TCP/IP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_server()

        # Contatori di messaggi
        self.message_count_inviati = 0
        self.message_count_ricevuti = 0

        self.debug = False
        
        # METODI:

    def debug_print(self, message):
        # Stampa tutti i messaggi di debug/errore.
        if self.debug:
            print("DEBUG (" + self.id + "): " + message)


    def all_nodes(self):
        # Restituisce una lista con tutti i nodi connessi con l'attuale
        return self.nodes_inbound + self.nodes_outbound

    def generate_id(self):
        # Genera un ID univoco per ogni nodo
        id = hashlib.sha512()
        t = self.host + str(self.porta) + str(random.randint(1, 99999999))
        id.update(t.encode('ascii'))
        return id.hexdigest()

    def init_server(self):
        """Inizializzazione del server TCP/IP per ricevere le connessioni.
        Si lega all'host e alla porta specificati"""
        print("Inizializzazione del nodo (" + self.id + ") sulla porta: " + str(self.porta) )
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.porta))
        self.sock.settimeout(10.0)
        self.sock.listen(1)

    def print_connections(self):
        # Stampa il numero di connessioni in entrata e in uscita che sono state effettuate.
        print("Panoramica della connessione del nodo: ")
        print("- Totale nodi connessi con noi: %d" % len(self.nodes_inbound))
        print("- Totale nodi a cui siamo connessi: %d" % len(self.nodes_outbound))

    def send_to_nodes(self, data, exclude=[]):
        """ Invia un messaggio a tutti i nodi connessi con l'attuale. 
        "data" è una variabile Python che è convertita in JSON che viene inviata a un altro nodo. 
        L'elenco di esclusione fornisce tutti i nodi a cui non deve essere inviato il messaggio."""
        self.message_count_inviati = self.message_count_inviati + 1
        for n in self.nodes_inbound:
            if n in exclude:
                self.debug_print("send_to_nodes: Escluso nodo nell'invio del messaggio")
            else:
                self.send_to_node(n, data)

        for n in self.nodes_outbound:
            if n in exclude:
                self.debug_print("send_to_nodes: Escluso nodo nell'invio del messaggio")
            else:
                self.send_to_node(n, data)

    def send_to_node(self, n, data):
        # Invia il messaggio al nodo n, se esiste.
        self.message_count_inviati = self.message_count_inviati + 1
        if n in self.nodes_inbound or n in self.nodes_outbound:
            n.send(data)
        else:
            self.debug_print("send_to_node: Impossibile inviare il messaggio, nodo non trovato!")
        

    def connect_with_node(self, host, porta, reconnect = True):
        """ Effettua una connessione con un altro nodo in esecuzione. Quando viene stabilita la connessione con il nodo si scambiano
            gli id. Prima inviamo il nostro id e poi riceviamo l'id del nodo a cui siamo connessi.
            Se reconnect == True, il nodo tenterà di riconnettersi ogni volta che la connessione viene interrotta."""
        
        if host == self.host and porta == self.porta:
            print("connect_with_node: impossibile connettersi con se stessi!")
            return False

        # Verifica che il nodo non sia già connesso con noi
        for node in self.nodes_outbound:
            if node.host == host and node.porta == porta:
                print("connect_with_node: Già connesso con questo nodo (" + node.id + ").")
                return True

        

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.debug_print("connessione a %s porta %s" % (host, porta))
            sock.connect((host, porta))

            # Scambio degli ID
            sock.send(self.id.encode('utf-8')) # Invia l'ID al nodo connesso
            connected_node_id = sock.recv(4096).decode('utf-8') # Riceve l'ID dal nodo connesso

            # Verifica che il nodo non sia già connesso con noi
            for node in self.nodes_inbound:
                if node.host == host and node.id == connected_node_id:
                    print("connect_with_node: Già connesso con questo nodo (" + node.id + ").")
                    return True    

            thread_client = self.create_new_connection(sock, connected_node_id, host, porta)
            thread_client.start()

            self.nodes_outbound.append(thread_client)

            # Se la riconnessione a questo host è richiesta, questo verrà aggiunto alla lista "reconnect_to_nodes"
            if reconnect:
                self.debug_print("connect_with_node: Riconnessione abilitata per il nodo " + host + ":" + str(porta))
                self.reconnect_to_nodes.append({
                    "host": host, "porta": porta, "tries": 0
                })

        except Exception as e:
            self.debug_print("TcpServer.connect_with_node: Impossibile connettersi con il nodo. (" + str(e) + ")")


    def disconnect_with_node(self, node):
        # Termina la connessione TCP/IP con il nodo specificato. Arresta il nodo e questo verrà eliminato dall'elenco nodes_outbound.
        if node in self.nodes_outbound:
            node.stop()

        else:
            self.debug_print("disconnect_with_node: Impossibile disconnettersi da questo nodo.")

    def stop(self):
            # Arresta questo nodo e termina tutti i nodi connessi.
            self.terminate_flag.set()

    def create_new_connection(self, connection, id, host, porta):
        """Quando viene effettuata una nuova connessione con un nodo o un nodo si sta connettendo con noi, viene utilizzato questo metodo
            per creare la nuova connessione effettiva. In questo caso verrà istanziata una "Connessione" per rappresentare la connessione del nodo."""
        return Connessione(self, connection, id, host, porta)

    def reconnect_nodes(self):
        """Questo metodo controlla se i nodi con lo stato di riconnessione attiva sono ancora connessi. 
            Se non sono collegati vengono riavviati."""
        for node_to_check in self.reconnect_to_nodes:
            found_node = False
            self.debug_print("reconnect_nodes: Verifica nodo " + node_to_check["host"] + ":" + str(node_to_check["porta"]))

            for node in self.nodes_outbound: # Controllo se il nodo è connesso
                if node.host == node_to_check["host"] and node.porta == node_to_check["porta"]:
                    found_node = True
                    node_to_check["trials"] = 0 # Reset del conteggio
                    self.debug_print("reconnect_nodes: Il nodo " + node_to_check["host"] + ":" + str(node_to_check["porta"]) + " è ancora connesso")

            if not found_node: # Riconnessione con il nodo
                node_to_check["trials"] += 1
                if self.node_reconnection_error(node_to_check["host"], node_to_check["porta"], node_to_check["trials"]):
                    self.connect_with_node(node_to_check["host"], node_to_check["porta"])

                else:
                    self.debug_print("reconnect_nodes: Rimuovo il nodo (" + node_to_check["host"] + ":" + str(node_to_check["porta"]) + ") dalla lista di riconnessione")
                    self.reconnect_to_nodes.remove(node_to_check)

    
    def run(self):
        """Il ciclo principale del thread che si occupa delle connessioni da altri nodi della rete. Quando un
            nodo è connesso, scambierà gli ID. Per prima cosa riceviamo l'ID del nodo e, in secondo luogo,
            invieremo il nostro ID."""
        while not self.terminate_flag.is_set():  # Controlla se il thread deve essere chiuso
            try:
                self.debug_print("In attesa di una connessione in arrivo")
                connection, client_address = self.sock.accept()

                self.debug_print("Connessioni inbound totali: " + str(len(self.nodes_inbound)))
                
                    
                # Scambio degli ID
                connected_node_id = connection.recv(4096).decode('utf-8') 
                connection.send(self.id.encode('utf-8')) 

                thread_client = self.create_new_connection(connection, connected_node_id, client_address[0], client_address[1])
                thread_client.start()

                self.nodes_inbound.append(thread_client)

            
            except socket.timeout:
                self.debug_print('Tempo scaduto')

            except Exception as e:
                raise e

            self.reconnect_nodes()

            time.sleep(0.01)

        print("Terminazione nodo...")
        for t in self.nodes_inbound:
            t.stop()

        for t in self.nodes_outbound:
            t.stop()

        time.sleep(1)

        for t in self.nodes_inbound:
            t.join()

        for t in self.nodes_outbound:
            t.join()

        self.sock.settimeout(None)   
        self.sock.close()
        print("Nodo terminato")


    def node_disconnected(self, node):
        """La classe Connessione non è in grado di determinare se si tratta di una connessione in entrata o in uscita.
        Questa funzione assicura che venga utilizzato il metodo corretto."""
        self.debug_print("node_disconnected: " + node.id)

        if node in self.nodes_inbound:
            del self.nodes_inbound[self.nodes_inbound.index(node)]

        if node in self.nodes_outbound:
            del self.nodes_outbound[self.nodes_outbound.index(node)]

    def node_message(self, node, data):
        # Questo metodo viene invocato quando un nodo ci invia un messagio.
        print("node_message: " + node.id + ": " + str(data))

    def node_reconnection_error(self, host, porta, trials):
        """Questo metodo viene richiamato quando si verifica un errore di riconnessione. La connessione al nodo è terminata e il
            flag per la riconnessione è impostato su True per quel nodo. Il nodo tenterà sempre di eseguire la riconnessione."""
        self.debug_print("node_reconnection_error: Riconnesione con il nodo " + host + ":" + str(porta) + " (trials: " + str(trials) + ")")
        return True

    def __str__(self):
        return 'Node: {}:{}'.format(self.host, self.porta)

    def __repr__(self):
        return '<Node {}:{} id: {}>'.format(self.host, self.porta, self.id)
