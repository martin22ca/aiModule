import os
import cv2
import json
import time
import socket
import requests
from pathlib import Path
from datetime import datetime, date
from classRecogLib.faceRecog import encodeFace, predictClass, findFaces, loadKNN, loadDetectionModel, loadRecognitionModel
from classRecogLib.utils import resizeAndPad, getMacAddr


class classroom():
    def __init__(self, idClassroom, commPipe, modelsDir):
        ipAddress = socket.gethostbyname(socket.gethostname()+".local")
        modelsDir = str(modelsDir)
        attendenceDir = str(Path.home())+ '/attendence/'

        if not os.path.exists(attendenceDir):
            os.makedirs(attendenceDir)

        todayDir = attendenceDir+str(date.today())+'/'

        self.idClassroom = idClassroom
        self.mainServerIp = None
        self.onTime = False
        self.ipAddr = ipAddress
        self.macAddr = getMacAddr()
        self.students = {}
        self.workDir = todayDir
        self.faceDetector = loadDetectionModel()
        self.faceRecognizer = loadRecognitionModel(modelsDir+'/models/')
        self.KNNModel = loadKNN(modelsDir+'/models/')
        self.prevTime = time.time()
        self.commPipe = commPipe

        if not os.path.exists(todayDir):
            os.makedirs(todayDir+'toSend/')
            os.makedirs(todayDir+'sent')
        else:
            print('Continue Day')
            self.loadPreviousData()

    def loadPreviousData(self):
        dirs =[self.workDir+'toSend/',self.workDir+'sent/'] 
        for dir in dirs:
            for stud in os.listdir(dir):
                try:
                    with open(dir+stud+'/info.json', 'r') as f:
                        student = json.load(f)
                        self.students[student['studentId']] = student
                        print('load:',stud)
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
                student = {

                    "studentId": studentId,
                    "classroomId": self.idClassroom,
                    "certainty": float(pred),
                    "timeOfEntry": str(datetime.now().replace(second=0, microsecond=0)),
                    "onTime": self.onTime,
                }
                self.students[studentId] = student
                if self.mainServerIp == None:
                    studentDir = self.workDir+'toSend/student-'+str(studentId)+'/'
                    os.makedirs(studentDir)
                    imgPath = studentDir+'student-picture.jpg'
                    with open(studentDir+"info.json", "w") as write_file:
                        json.dump(student, write_file, indent=4)
                    face = resizeAndPad(face, (160, 160), 0)
                    cv2.imwrite(imgPath,face, [cv2.IMWRITE_JPEG_QUALITY, 93])
                else:
                    studentDir = self.workDir+'sent/student-'+str(studentId)+'/'
                    os.makedirs(studentDir)
                    imgPath = studentDir+'student-picture.jpg'
                    with open(studentDir+"info.json", "w") as write_file:
                        json.dump(student, write_file, indent=4)
                    face = resizeAndPad(face, (160, 160), 0)
                    cv2.imwrite(imgPath,face, [cv2.IMWRITE_JPEG_QUALITY, 93])
                    url = 'http://'+self.mainServerIp+'newStudent'
                    file = {'media': open(imgPath, 'rb')}
                    response = requests.post(url,data=student,files=file)
                    print(response.status_code, response.reason)


                return None
        return None

    def detectFace(self, image):
        faces = findFaces(image, self.faceDetector)
        for i, face in enumerate(faces):
            now = time.time()
            if (now - self.prevTime) > 0.5:
                self.prevTime = now
                encoding = encodeFace(face, self.faceRecognizer)
                prediction = predictClass(encoding, self.KNNModel)
                if prediction != None:
                    self.validateStudent(face, prediction[0], prediction[1])


if __name__ == '__main__':
    t = classroom()
    t.classLoop()
