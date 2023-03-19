import os
import cv2
import json
import time
import requests
import base64
from pathlib import Path
from datetime import datetime, date
from socket import gethostbyname,gethostname
from recogLib.faceRecog import encodeFace, predictClass, findFaces, loadKNN, loadDetectionModel, loadRecognitionModel
from recogLib.utils import resizeAndPad

class Classroom():
    def __init__(self, idClassroom,commPipe,serverIp):
        ipAddress = gethostbyname(gethostname()+".local")
        attendenceDir = str(Path.home())+ '/attendence/'

        if not os.path.exists(attendenceDir):
            os.makedirs(attendenceDir)

        self.idClassroom = idClassroom
        self.close = False
        self.mainServerIp = serverIp
        self.onTime = True
        self.ipAddr = ipAddress

        self.students = {}
        self.todayDir = attendenceDir+str(date.today())+'/'
        self.faceDetector = loadDetectionModel()
        self.faceRecognizer = loadRecognitionModel()
        self.KNNModel = loadKNN()
        self.prevTime = time.time()
        self.commPipe = commPipe

        if not os.path.exists(self.todayDir):
            os.makedirs(self.todayDir)

        else:
            self.loadPreviousData()

    def loadPreviousData(self):
        if os.path.exists(self.todayDir+'closed.json'):
            self.onTime = False
            print('Students are now Late')
            
        for stud in os.listdir(self.todayDir):
            try:
                with open(dir+stud+'/info.json', 'r') as f:
                    student = json.load(f)
                    self.students[student['studentId']] = student
            except:
                continue

    def classLoop(self):
        cam = cv2.VideoCapture(0)
        while (cam.isOpened()) and self.close == False:
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
            0: self.setClose,
        }
        return switcher[msg[0]](msg[1])

    def setClose(self,inst):
        self.close = True 

    def validateStudent(self, face, studentId, pred,dst):
        if studentId not in self.students.keys():
            if float(pred) > 0.8:
                print('New student:', studentId)
                student = {

                    "studentId": 1,
                    "classroomIp":self.ipAddr,
                    "classroomId": self.idClassroom,
                    "certainty": float(pred),
                    "timeOfEntry": str(datetime.now().replace(second=0, microsecond=0)),
                    "onTime": self.onTime,
                    "distance": dst.tolist()[0]
                }
                self.students[studentId] = student
                studentDir = self.todayDir+'student-'+str(studentId)+'/'
                os.makedirs(studentDir)
                imgPath = studentDir+'student-picture.jpg'
                with open(studentDir+"info.json", "w") as write_file:
                    json.dump(student, write_file, indent=4)
                face = resizeAndPad(face, (200, 200), 0)
                cv2.imwrite(imgPath,face, [cv2.IMWRITE_JPEG_QUALITY, 93])
                url = 'http://'+self.mainServerIp+':5000/attendece/newAttendence'

                #encode image
                string_img = base64.b64encode(cv2.imencode('.jpg', face)[1]).decode()
                student['image'] = string_img

                #send json to server
                response = requests.post(url , json=student)
                return None
        return None

    def detectFace(self, image):
        faces = findFaces(image, self.faceDetector)
        for i, face in enumerate(faces):
            now = time.time()
            if (now - self.prevTime) > 0.6:
                self.prevTime = now
                encoding = encodeFace(face, self.faceRecognizer)
                prediction = predictClass(encoding, self.KNNModel)
                if prediction != None:
                    self.validateStudent(face, prediction[0], prediction[1],prediction[2])


if __name__ == '__main__':
    t = Classroom()
    t.classLoop()
