import os
from time import sleep
from klein import Klein
from pathlib import Path
from zeroConfDNS import FlaskServerListener
from multiprocessing import Process, Pipe,freeze_support
from daemonManager.classroom import Classroom
from daemonManager.config import configServer
from zeroconf import ServiceBrowser, Zeroconf

CONFIGPATH = (__file__.split("app.py"))[0] 

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def runserver(interface, port, commPipe):
    logfilename = open('server'+ str(port) + '.log', 'a')
    app = Klein()

    @app.route('/close', methods=['GET'])
    def close(request):
        commPipe.send([0, 0])
        return 'Closing Server'
    
    @app.route('/hello', methods=['GET'])
    def helloF(request):
        commPipe.send([1, 1])
        print("me saludan")
        return True

    app.run(interface, port, logfilename)

if __name__ == '__main__':
    freeze_support()
    zeroconf = Zeroconf()
    listener = FlaskServerListener('flaskServer')
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    print('serching for server')
    while listener.serverIp is None:
        sleep(1)
    
    serverIP = listener.serverIp

    del listener,browser,zeroconf

    idClassroom = configServer(serverIP,CONFIGPATH+'config.ini')

    MODELSPATH = Path(__file__).parent.resolve()
    
    aPipe, bPipe = Pipe(duplex=True)
    
    todayClass = Classroom(idClassroom, aPipe , serverIP)

    serverLoop = Process(target=runserver, args=('0.0.0.0', 3023, bPipe))
    serverLoop.start()
    todayClass.classLoop()
    serverLoop.terminate()