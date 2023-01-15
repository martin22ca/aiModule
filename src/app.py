from faceRecogLIb.classroom import classroom
from multiprocessing import Process, Queue
from klein import Klein
from dotenv import load_dotenv

load_dotenv()


def runserver(interface, port,communicationQueue):
    logfilename = open('localhost' + str(port) + '.log', 'a')
    app = Klein()
    @app.route('/',methods=['GET'])
    def pg_root(request):
        communicationQueue.put([1,0])
        return 'IM WORKING'

    @app.route('/stud',methods=['GET'])
    def pg_stud(request):
        communicationQueue.put([0,0])
        return 'IM WORKING'

    app.run(interface, port, logfilename)

def loopClass(classroom,queue):
    while True:
        classroom.detectFace()
        print(queue.get())

if __name__ == '__main__':
    communicationQueue = Queue()
    communicationQueue.put([42, None, 'hello'])
    todayClass = classroom()

    serverLoop = Process(target=runserver, args=('localhost',9022,communicationQueue))
    serverLoop.start()
    todayClass.classLoop(communicationQueue)



    
    