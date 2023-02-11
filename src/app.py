from classRecogLib.classroom import classroom
import pathlib
import json
from multiprocessing import Process, Pipe
from klein import Klein


def runserver(interface, port, commPipe):
    logfilename = open('localhost' + str(port) + '.log', 'a')
    app = Klein()

    @app.route('/', methods=['GET'])
    def pg_root(request):
        commPipe.send([1, 0])
        request.setResponseCode(200)
        return 'Students are now Late'

    @app.route('/stud', methods=['GET'])
    def pg_stud(request):
        commPipe.send([0, 0])
        if commPipe.poll(timeout=5):
            stude = commPipe.recv()
            request.setResponseCode(200)
            return json.dumps(stude)
        else:
            request.setResponseCode(404)
            return 'Time Out'

    app.run(interface, port, logfilename)


if __name__ == '__main__':
    aPipe, bPipe = Pipe(duplex=True)
    todayClass = classroom(aPipe, pathlib.Path(__file__).parent.resolve())

    serverLoop = Process(target=runserver, args=('localhost', 9022, bPipe))
    serverLoop.start()
    todayClass.classLoop()
