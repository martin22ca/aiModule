import os
from time import sleep
from klein import Klein
from pathlib import Path
from zeroConfDNS import FlaskServerListener
from multiprocessing import Process, Pipe, freeze_support
from daemonManager.classroom import Classroom
from daemonManager.config import configServer
from zeroconf import ServiceBrowser, Zeroconf

CONFIGPATH = (__file__.split("app.py"))[0]

__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))


def runserver(interface, port, commPipe):
    logfilename = open('server' + str(port) + '.log', 'a')
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
    print(
        # +------------------------------------------------+
        # | Bienvenido al programa de Reconocmiento facial!|
        # | -----------------------------------------------|
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # |                                                |
        # +------------------------------------------------+
    )
    freeze_support()
    zeroconf = Zeroconf()
    listener = FlaskServerListener('flaskServer')
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    print('Serching for server')
    count = 0
    while listener.serverIp is None or count > 60:
        try:
            sleep(1)
            count =+ 1 
        except Exception as e:
            print(f"Exception occurred: {e}")
            # Reset the program or take appropriate action

    serverIP = listener.serverIp

    del listener, browser, zeroconf

    idClassroom = configServer(serverIP, CONFIGPATH)

    MODELSPATH = Path(__file__).parent.resolve()

    aPipe, bPipe = Pipe(duplex=True)

    todayClass = Classroom(idClassroom, aPipe, serverIP, CONFIGPATH)

    serverLoop = Process(target=runserver, args=(
        '0.0.0.0', 3023, bPipe))
    serverLoop.start()
    todayClass.classLoop()
    serverLoop.terminate()
