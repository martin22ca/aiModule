import cv2
import math
import dlib
import pickle
import numpy as np
import mediapipe as mp
from classRecogLib.utils import getAngle, getNewLocations, rotate_image


def loadKNN(baseDir):
    """
    Returns an K-Nearest Neighbors Model with the encodings for the faces

    :return: an K-Nearest Neighbors Model with the encodings for the faces
    """
    with (open(baseDir + 'knnPickleFile.pickle', 'rb')) as f:
        knn = pickle.load(f)
        return knn


def loadRecognitionModel(baseDir):
    """
    Returns the models required to encode the faces

    :return: the models required to encode the faces
    """
    pose_predictor_5_point = dlib.shape_predictor(
        baseDir+'shape_predictor_5_face_landmarks.dat')
    face_encoder = dlib.face_recognition_model_v1(
        baseDir+'dlib_face_recognition_resnet_model_v1.dat')

    return pose_predictor_5_point, face_encoder


def loadDetectionModel():
    """
    Returns the models required to locate the faces in an image

    :return: the models required to locate the faces in an image
    """
    getPoints = mp.solutions.face_detection.get_key_point
    mp_face_detection = mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5).process
    return mp_face_detection, getPoints


def predictClass(encoding, knn):
    """
    Returns an array of the predicted Student and its probabilty

    :param img: An image (as a numpy array)
    :savePath str: An string of weather you should store the images or not 
    :return: A list of tuples of found face locations in css (top, right, bottom, left) order
    """
    encoding = np.array(encoding).reshape(1, -1)
    probabilty = np.max(knn.predict_proba(encoding)[0])
    prediction = knn.predict(encoding)[0]

    return [prediction, probabilty]


def findFaces(image, faceDetector):
    """
    Returns an array of bounding boxes of human faces in a image

    :param img: An image (as a numpy array)
    :savePath str: An string of weather you should store the images or not 
    :return: A list of tuples of found face locations in css (top, right, bottom, left) order
    """

    face_detection = faceDetector[0]
    getPoints = faceDetector[1]
    facesFound = []

    imageGray = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    imgHeight, imgWidth, c = image.shape

    results = face_detection(imageGray)
    if results.detections:
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            xMin = int(bbox.xmin * imgWidth-10)
            yMin = int(bbox.ymin * imgHeight-10)
            w = int(bbox.width * imgWidth+10)
            h = int(bbox.height * imgHeight+10)
            rightEye = getPoints(detection, 0).x, getPoints(detection, 0).y
            lefEye = getPoints(detection, 1).x, getPoints(detection, 1).y
            angle = getAngle(lefEye, rightEye)
            imageC = rotate_image(image, angle*180/math.pi)
            centerImage = (imgWidth)/2, (imgHeight)/2
            newX, newY = getNewLocations(
                [(xMin+w/2), (yMin+h/2)], centerImage, -angle)
            crop = imageC[int(newY-h/2):int(newY+h/2),
                          int(newX-w/2):int(newX+w/2)]
            facesFound.append(crop)

    return facesFound


def _raw_face_landmarks(face_image, pose_predictor_5_point):
    h, w, c = face_image.shape
    faceLoc = dlib.rectangle(0, 0, w, h)

    return pose_predictor_5_point(face_image, faceLoc)


def encodeFace(face_image, encoderModel, num_jitters=1):
    """
    Given an image, return the 128-dimension face encoding.

    :param face_image: The image that contains one face
    :param num_jitters: How many times to re-sample the face when calculating encoding. Higher is more accurate, but slower (i.e. 100 is 100x slower)
    :return: A list of 128-dimensional face encodings
    """
    face_encoder = encoderModel[1]
    pose_predictor_5_point = encoderModel[0]
    raw_landmarks = _raw_face_landmarks(face_image, pose_predictor_5_point)
    encoding = face_encoder.compute_face_descriptor(
        face_image, raw_landmarks, num_jitters)
    return encoding
