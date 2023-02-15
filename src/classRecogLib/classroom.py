import os
import cv2
import json
import time
import socket
from datetime import datetime, date
from classRecogLib.faceRecog import encodeFace, predictClass, findFaces, loadKNN, loadDetectionModel, loadRecognitionModel
from classRecogLib.utils import resizeAndPad, getMacAddr


class classroom():
    def __init__(self, commPipe, workDir):
        ipAddress = socket.gethostbyname(socket.gethostname()+".local")
        workDir = str(workDir)
        attendenceDir = workDir + '/attendence/'

        if not os.path.exists(attendenceDir):
            os.makedirs(attendenceDir)
        todayDir = attendenceDir+str(date.today())+'/'

        with open(workDir+'/config.json') as f:
            parsedJson = json.load(f)
            self.idClassroom = parsedJson['classroom']

        self.mainServerIp = None
        self.onTime = False
        self.ipAddr = ipAddress
        self.macAddr = getMacAddr()
        self.students = {}
        self.workDir = todayDir
        self.faceDetector = loadDetectionModel()
        self.faceRecognizer = loadRecognitionModel(workDir+'/models/')
        self.KNNModel = loadKNN(workDir+'/models/')
        self.prevTime = time.time()
        self.commPipe = commPipe

        if not os.path.exists(todayDir):
            os.makedirs(todayDir)
        else:
            print('Continue Day')
            self.loadPreviousData()

    def loadPreviousData(self):
        for stud in os.listdir(self.workDir):
            try:
                with open(self.workDir+stud+'/info.json', 'r') as f:
                    student = json.load(f)
                    self.students[student['studentId']] = student
            except:
                continue

    def classLoop(self):
        cam = cv2.VideoCapture(0)
        while (cam.isOpened()):
            if self.commPipe.poll():
                res = self.commPipe.recv()
                self.manageMsg(res)
            else:
                success, image = cam.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue
                else:
                    self.detectFace(image)

    def manageMsg(self, msg):
        switcher = {
            0: self.getClassRoom,
            1: self.setLate,
            2: self.getStudents,
        }
        return switcher[msg[0]](msg[1])

    def getStudents(self, inst):
        print('entre')
        self.commPipe.send(self.students)
        return None

    def setLate(self, inst):
        self.onTime = False
        return None

    def getClassRoom(self, inst):
        self.mainServerIp = inst
        thisClassroom = {
            "id": self.idClassroom,
            "ipAddr": self.ipAddr,
            "macAddr": self.macAddr
        }
        self.commPipe.send(thisClassroom)
        return None

    def validateStudent(self, face, studentId, pred):
        if studentId not in self.students.keys():
            if float(pred) > 0.8:
                print('New student:', studentId)
                studentDir = self.workDir+'student-'+str(studentId)+'/'
                os.makedirs(studentDir)
                imgPath = studentDir+'student-picture.jpg'
                student = {
                    "studentId": studentId,
                    "classroomId": self.idClassroom,
                    "certainty": float(pred),
                    "timeOfEntry": str(datetime.now().replace(second=0, microsecond=0)),
                    "onTime": self.onTime,
                    "pathToImg": imgPath
                }
                self.students[studentId] = student
                with open(studentDir+"info.json", "w") as write_file:
                    json.dump(student, write_file, indent=4)

                face = resizeAndPad(face, (200, 200), 0)
                cv2.imwrite(studentDir+'student-picture.jpg',
                            face, [cv2.IMWRITE_JPEG_QUALITY, 93])

                if self.mainServerIp != None:
                    print('MANDO DATA')

                return None
        return None

    def detectFace(self, image):
        faces = findFaces(image, self.faceDetector)
        for i, face in enumerate(faces):
            now = time.time()
            if (now - self.prevTime) > 0.5:
                self.prevTime = now
                encoding = encodeFace(face, self.faceRecognizer)
                prediction, probabilty = predictClass(encoding, self.KNNModel)
                self.validateStudent(face, prediction, probabilty)


if __name__ == '__main__':
    t = classroom()
    t.classLoop()
