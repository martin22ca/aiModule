import os
import cv2
import json
import time
import socket
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime,date
from faceRecogLIb.faceRecogLib import encodeFace,predictClass,findFaces,loadKNN,loadDetectionModel,loadRecognitionModel

class classroom():
    def __init__(self):
        load_dotenv()
        ip_address = socket.gethostbyname(socket.gethostname()+".local")
        id_classroom = os.getenv('CLASSROOM')
        basePath = str(Path.home())+'/Aistencias/'

        if not os.path.exists(basePath):
            os.makedirs(basePath)
        todayDir = basePath+str(date.today())+'/'

        self.id = id_classroom
        self.ip = ip_address
        self.students = {}
        self.workDir = todayDir
        self.faceDetector = loadDetectionModel()
        self.faceRecognizer = loadRecognitionModel()
        self.KNNModel = loadKNN()
        self.prevTime = time.time()
        self.onTime = True

        if not os.path.exists(todayDir):
            os.makedirs(todayDir)
        else:
            print('continue Day')
            self.loadPreviousData()
    
    def getStudents(self):
        print(self.students)

    def loadPreviousData(self):
        for stud in os.listdir(self.workDir):
            try:
                with open(self.workDir+stud+'/info.json','r') as f:
                    student = json.load(f)
                    self.students[student['studentId']] = student
            except:
                continue

    def classLoop(self,communicationQueue):
        cam = cv2.VideoCapture(0)
        while(cam.isOpened()):
            if communicationQueue.empty():
                success, image = cam.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    continue
                else:
                    self.detectFace(image)
            else:
                res = communicationQueue.get()
                self.manageMsg(res)
    
    def manageMsg(self, msg):
        instruct = msg[0]
        value = msg[1]

        if instruct == 0:
            self.getStudents()
            return None
        if instruct == 1:
            self.onTime = value
            return None

    def validateStudent(self,face,studentId,pred):
        if studentId not in self.students.keys():
            if float(pred) > 0.8:
                student = {
                    "studentId": studentId,
                    "classId": self.id,
                    "certenty": float(pred),
                    "timeOfEntry": str(datetime.now().replace(second=0, microsecond=0)),
                    "onTime":self.onTime
                }
                self.students[studentId] = student
                studentDir = self.workDir+'student-'+str(studentId)+'/'
                os.makedirs(studentDir)
                with open(studentDir+"info.json", "w") as write_file:
                    json.dump(student, write_file, indent=4)
                cv2.imwrite(studentDir+'student-picture.jpg',face)
        
    def detectFace(self,image):
        faces = findFaces(image,self.faceDetector)
        for i,face in enumerate(faces):
            now =time.time()
            if (now - self.prevTime) > 0.5:
                self.prevTime = now
                encoding =encodeFace(face,self.faceRecognizer)
                prediction,probabilty = predictClass(encoding,self.KNNModel)
                self.validateStudent(face,prediction,probabilty)


if __name__ == '__main__':
    t = classroom()
    t.classLoop()

