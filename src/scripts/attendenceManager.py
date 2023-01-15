import os
import sys
import socket
from multiprocessing.connection import Listener
from dotenv import load_dotenv
from scripts.faceRecogLIb.classroom import classroom

address = ('localhost', 6000)     # family is deduced to be 'AF_INET'
listener = Listener(address, authkey=b'secret password')
conn = listener.accept()

def listenChagnes():
    while True:
        msg = conn.recv()
        print(msg)
        # do something with msg
        if msg == 'close':
            
            conn.close()
            break
    listener.close()

listenChagnes()