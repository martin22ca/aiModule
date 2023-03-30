import os
from time import sleep
from klein import Klein
from pathlib import Path
from configparser import ConfigParser
from zeroConfDNS import FlaskServerListener
from multiprocessing import Process, Pipe,freeze_support
from daemonManager.classroom import Classroom
from zeroconf import ServiceBrowser, Zeroconf

CONFIGPATH = (__file__.split("app.py"))[0] 

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def runserver(interface, port, commPipe):
    logfilename = open('server'+ str(port) + '.log', 'a')
    app = Klein()

    @app.route('/close', methods=['GET'])
    def helloF(request):
        
        commPipe.send([0, 0])
        return 'Closing Server'

    app.run(interface, port, logfilename)

if __name__ == '__main__':
    freeze_support()

    configur = ConfigParser()
    configur.read(os.path.join(__location__,'config.ini'))

    CLASSROOMNUM = configur.getint('CONFIG','numClass')
    CLASSROOMNAME = configur.get('CONFIG','nameClass')
    MODELVERSION = configur.get('VERSION','knnModel')

    MODELSPATH = Path(__file__).parent.resolve()

    zeroconf = Zeroconf()
    listener = FlaskServerListener('flaskServer')
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

    print('serching for server')
    while listener.serverIp is None:
        sleep(1)
    

    serverIP = listener.serverIp

    del listener,browser,zeroconf
    
    aPipe, bPipe = Pipe(duplex=True)
    
    todayClass = Classroom(CLASSROOMNUM, CLASSROOMNAME,MODELVERSION, aPipe , serverIP)

    serverLoop = Process(target=runserver, args=('0.0.0.0', 9022, bPipe))
    serverLoop.start()
    todayClass.classLoop()
    serverLoop.terminate()