from multiprocessing import Process, Pipe, freeze_support
from daemonManager.classroom import Classroom
from daemonManager.config import serverSetup
from platformdirs import *
from pathlib import Path
from klein import Klein
from time import sleep
import os

CONFIGPATH = (__file__.split("app.py"))[0]
PORT = '5000'
DATA_DIR = user_data_dir("faceRecogApp", "mca_INC")

__location__ = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))

def runserver(interface, port, commPipe):
    logfilename = open(DATA_DIR+'/server' + str(port) + '.log', 'a')
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
    try:
        freeze_support()
        print("""
            +---------------------------------------------------+
            | Bienvenido al programa de Reconocmiento facial!   |
            +---------------------------------------------------+
            """)
        sleep(2)
        configs = serverSetup(CONFIGPATH, DATA_DIR).configServer()
        if configs == None:
            sleep(5)
        else:
            MODELSPATH = Path(__file__).parent.resolve()
            aPipe, bPipe = Pipe(duplex=True)
            todayClass = Classroom(configs, aPipe, DATA_DIR)
            serverLoop = Process(target=runserver, args=(
                '0.0.0.0', 3023, bPipe))

            serverLoop.start()
            todayClass.classLoop()
            serverLoop.terminate()
    except Exception as e:
        print("Error de sistema:", e)
        sleep(10)
