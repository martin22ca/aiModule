import tomli
from json import dumps
from klein import Klein
from pathlib import Path
from multiprocessing import Process, Pipe
from classroomLib.classroom import classroom


def runserver(interface, port, commPipe):
    logfilename = open('localhost' + str(port) + '.log', 'a')
    app = Klein()

    @app.route('/hello', methods=['POST'])
    def helloF(request):
        content = request.content.read().decode("utf-8")
        commPipe.send([0, content])
        if commPipe.poll(timeout=5):
            thisClass = commPipe.recv()
            print(thisClass)
            request.setResponseCode(200)
            return dumps(thisClass)
        else:
            request.setResponseCode(500)
            return 'Time Out'

    @app.route('/late', methods=['GET'])
    def statusLate(request):
        commPipe.send([1,None])
        request.setResponseCode(200)
        return 'Students are now Late'

    @app.route('/stud', methods=['GET'])
    def getStudents(request):
        commPipe.send([2,None])
        if commPipe.poll(timeout=5):
            stude = commPipe.recv()
            request.setResponseCode(200)
            return dumps(stude)
        else:
            request.setResponseCode(400)
            return 'Time Out'

    app.run(interface, port, logfilename)


if __name__ == '__main__':
    fp = open("config.toml", mode="rb")
    config = tomli.load(fp)
    fp.close()

    aPipe, bPipe = Pipe(duplex=True)
    CLASSROOMNUM = config['constant']['classroom']
    MODELSPATH = Path(__file__).parent.resolve()
    
    todayClass = classroom(CLASSROOMNUM,aPipe, MODELSPATH)

    serverLoop = Process(target=runserver, args=('localhost', 9022, bPipe))
    serverLoop.start()
    todayClass.classLoop()
