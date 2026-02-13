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
        self.server = xmlrpc.client.ServerProxy(f'http://{address[0]}:{address[1]}')

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
                response = self.server.ping()
                print("Server is alive:", response)
                self.server_active = True
            except Exception as e:
                print("Failed to ping server:", e)
                self.server_active = False
            time.sleep(5)

    def stop(self):
        self.thread_running = False
        
    
    def send_command(self, cmd_name, params):
        """
        Called by flask when a command is to be sent
        will receive the arguments already converted to the correct type
        """
        
        print("Calling rpc server with command:", cmd_name, "and params:", params)

        response = self.server.add_command(cmd_name, params)
        print("Received response from rpc server:", response)
        
        return response
        