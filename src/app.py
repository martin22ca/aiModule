import tomli
from time import sleep
from klein import Klein
from pathlib import Path
from zeroConfDNS import FlaskServerListener
from multiprocessing import Process, Pipe,freeze_support
from daemonManager.classroom import Classroom
from zeroconf import ServiceBrowser, Zeroconf

CONFIGPATH = (__file__.split("app.py"))[0] 

def runserver(interface, port, commPipe):
    logfilename = open('0.0.0.0:' + str(port) + '.log', 'a')
    app = Klein()

    @app.route('/close', methods=['GET'])
    def helloF(request):
        commPipe.send([0, 0])
        return 'Closing Server'

    app.run(interface, port, logfilename)

if __name__ == '__main__':
    freeze_support()
    fp = open(CONFIGPATH+"config.toml", mode="rb")
    config = tomli.load(fp)
    fp.close()

    CLASSROOMNUM = config['constant']['classroom']
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
    CLASSROOMNUM = config['constant']['classroom']
    
    todayClass = Classroom(CLASSROOMNUM, aPipe , serverIP)

    serverLoop = Process(target=runserver, args=('localhost', 9022, bPipe))
    serverLoop.start()
    todayClass.classLoop()
    serverLoop.terminate()