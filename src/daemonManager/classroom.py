import os
import cv2
import json
import time
import requests
import base64
from pathlib import Path
from datetime import datetime, date
from recogLib.faceRecog import encodeFace, predictClass, findFaces, loadKNN, loadDetectionModel, loadRecognitionModel
from recogLib.utils import resizeAndPad


class Classroom():
    def __init__(self, idClassroom, commPipe, serverIp, configPath):

        attendenceDir = str(Path.home()) + '/attendence/'

        if not os.path.exists(attendenceDir):
            os.makedirs(attendenceDir)

        self.idClassroom = idClassroom
        self.close = False
        self.mainServerIp = serverIp
        self.onTime = True

        self.students = {}
        self.configPath = configPath
        self.todayDir = attendenceDir+str(date.today())+'/'
        self.faceDetector = loadDetectionModel()
        self.faceRecognizer = loadRecognitionModel(configPath)
        self.KNNModel = loadKNN(configPath)
        self.prevTime = time.time()
        self.commPipe = commPipe

        if not os.path.exists(self.todayDir):
            os.makedirs(self.todayDir)
        else:
            print("continue")
            self.loadPreviousData()

    def loadPreviousData(self):
        for stud in os.listdir(self.todayDir):
            try:
                with open(self.todayDir+stud+'/info.json', 'r') as f:
                    student = json.load(f)
                    self.students[student['studentId']] = student
            except:
                continue

    def classLoop(self):
        camera_index = self.find_camera_index()
        if camera_index != -1:
            cam = cv2.VideoCapture(camera_index)
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
            closingTime = time.time()
            timerDuration = 40*60
            print("Closing Server in 40 min.")
            while (cam.isOpened()):
                elapsedTime = time.time() - closingTime
                if elapsedTime >= timerDuration:
                    # Exit the program
                    print("Closing Server.")
                    cam.release()
                    os._exit(0)
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
        else:
            print("No Camera available!")
            print("The program will close")
            time.sleep(10)
            

    def manageMsg(self, msg):
        switcher = {
            0: self.setClose,
            1: self.hello,
        }
        return switcher[msg[0]](msg[1])

    def setClose(self, inst):
        self.close = True

    def hello(self, inst):
        print("They Said Hello.")

    def validateStudent(self, face, studentId, pred):
        if studentId not in self.students.keys():
            print('New student:', studentId)
            student = {
                "studentId": str(studentId),
                "idClassroom": self.idClassroom,
                "certainty": float(pred),
                "timeOfEntry": str(datetime.now().replace(second=0, microsecond=0)),
                "onTime": self.onTime,
            }

            self.students[studentId] = student
            studentDir = self.todayDir+'student-'+str(studentId)+'/'
            os.makedirs(studentDir)
            imgPath = studentDir+'student-picture.jpg'
            with open(studentDir+"info.json", "w") as write_file:
                json.dump(student, write_file, indent=4)
            face = resizeAndPad(face, (200, 200), 0)
            cv2.imwrite(imgPath, face, [cv2.IMWRITE_JPEG_QUALITY, 93])
            url = 'http://'+self.mainServerIp+':5000/attendece/newAttendence'

            # encode image
            string_img = base64.b64encode(
                cv2.imencode('.jpg', face)[1]).decode()
            student['image'] = string_img
            # send json to server
            response = requests.post(url, json=student)
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
                    self.validateStudent(face, prediction[0], prediction[1])

    def find_camera_index(self):
        num_cameras = 5  # Set a reasonable upper limit for camera indices

        for i in range(num_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.release()
                return i

        # No valid camera found
        return -1


if __name__ == '__main__':
    t = Classroom()
    t.classLoop()
