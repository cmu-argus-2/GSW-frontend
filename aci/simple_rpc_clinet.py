"""
Need to find a better name for this file later on
this is the file that will implement a class used to call the simple rpc server

it will have a thread calling ping function every 5 seconds to check if the server is alive
if the server is not alive it will switch the status of the light in the ui

"""


import xmlrpc.client
import threading
import time

address = ("localhost", 8000)



class SimpleRPCClient:
    """Should find a better name for this class"""


    def __init__(self, address):
        self.address = address
        self.server = xmlrpc.client.ServerProxy(
            f'http://{address[0]}:{address[1]}',
            allow_none=True
        )
        self._lock = threading.Lock()  # ServerProxy is not thread-safe

        self.thread_running = True
        threading.Thread(target=self.ping_server, daemon=True).start()
        self.server_active = False
        
    #--------------------------------------------------------
    #                   Thread stuff
    #
    #--------------------------------------------------------
    
    def ping_server(self):
        while self.thread_running:
            try:
                with self._lock:
                    response = self.server.ping()
                print("Server is alive:", response)
                self.server_active = True
            except Exception as e:
                print("Failed to ping server:", e)
                self.server_active = False
            time.sleep(5)

    def stop(self):
        self.thread_running = False

    def update_address(self, ip, port):
        """Update the XML-RPC server address used by this client."""
        self.address = (ip, int(port))
        self.server = xmlrpc.client.ServerProxy(
            f'http://{ip}:{port}',
            allow_none=True
        )
        
    
    def send_command(self, cmd_name, params):
        """
        Called by flask when a command is to be sent
        will receive the arguments already converted to the correct type
        """
        
        print("Calling rpc server with command:", cmd_name, "and params:", params)

        with self._lock:
            response = self.server.add_command(cmd_name, params)
        print("Received response from rpc server:", response)

        return response

    def get_command_definitions(self):
        """
        Request command metadata from the SimpleRPC server.

        The SimpleRPC server should expose an XML-RPC method named
        `get_command_definitions` that returns an XML-RPC compatible array of
        structs with this shape:

        [
            {
                "name": "SET_MODE",
                "id": 7,
                "size": 4,
                "precondition": "",  # use empty string if not needed
                "arguments": [
                    {"name": "mode_id", "type": "B"},
                    {"name": "timeout", "type": "H"}
                ]
            }
        ]

        Expected fields per command:
        - name: str
        - id: int
        - size: int
        - precondition: str
        - arguments: list[dict] where each dict contains:
            - name: str
            - type: str

        The `type` field should use the same format codes the frontend/backend
        already understands:
        - integers: b, B, ?, h, H, i, I, l, L, q, Q, n, N
        - floats: e, d, F, D
        - strings: s, p
        """
        with self._lock:
            response = self.server.get_command_definitions()
        print("Received command definitions from rpc server")
        return response

    def get_pending_ack(self):
        """Pop and return the oldest pending ACK from the backend, or None if empty."""
        with self._lock:
            return self.server.get_pending_ack()

    def get_transaction_status(self, tid):
        """Return current state of an RX transaction by tid."""
        with self._lock:
            return self.server.get_transaction_status(tid)

    def get_new_packets(self):
        """Drain and return all decoded packets queued since the last call."""
        with self._lock:
            return self.server.get_new_packets()

    def set_sc_callsign(self, callsign):
        """Set the active satellite callsign on the backend."""
        with self._lock:
            return self.server.set_sc_callsign(callsign)

    def get_sc_callsign(self):
        """Return the currently selected satellite callsign from the backend."""
        with self._lock:
            return self.server.get_sc_callsign()
