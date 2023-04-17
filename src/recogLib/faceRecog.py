import cv2
import math
import dlib
import pickle
import numpy as np
import sklearn
import mediapipe as mp
from collections import Counter
from recogLib.utils import getAngle, getNewLocations, rotate_image, resizeAndPad

MODELSDIR = (__file__.split("faceRecog.py"))[0] + 'models/'

def loadKNN():
    """
    Returns an K-Nearest Neighbors Model with the encodings for the faces

    :return: an K-Nearest Neighbors Model with the encodings for the faces
    """

    with (open(MODELSDIR + 'knnPickleFile.pickle', 'rb')) as f:
        knn = pickle.load(f)
    with(open(MODELSDIR + 'namesFile.pickle', 'rb')) as f:
        names = pickle.load(f)
    return knn,names


def loadRecognitionModel():
    """
    Returns the models required to encode the faces

    :return: the models required to encode the faces
    """
    pose_predictor_5_point = dlib.shape_predictor(
        MODELSDIR+'shape_predictor_5_face_landmarks.dat')
    face_encoder = dlib.face_recognition_model_v1(
        MODELSDIR+'dlib_face_recognition_resnet_model_v1.dat')

    return pose_predictor_5_point, face_encoder


def loadDetectionModel():
    """
    Returns the models required to locate the faces in an image

    :return: the models required to locate the faces in an image
    """
    getPoints = mp.solutions.face_detection.get_key_point
    mp_face_detection = mp.solutions.face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.8).process
    return mp_face_detection, getPoints

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
            xMin = int(bbox.xmin * imgWidth)
            yMin = int(bbox.ymin * imgHeight)
            w = int(bbox.width * imgWidth)
            h = int(bbox.height * imgHeight)
            try:
                asp = h/w
                if asp < 2 or asp > 1/2:
                    rightEye = getPoints(
                        detection, 0).x, getPoints(detection, 0).y
                    lefEye = getPoints(
                        detection, 1).x, getPoints(detection, 1).y
                    angle = getAngle(lefEye, rightEye)
                    imageC = rotate_image(image, angle*180/math.pi)
                    centerImage = (imgWidth)/2, (imgHeight)/2
                    newX, newY = getNewLocations(
                        [(xMin+w/2), (yMin+h/2)], centerImage, -angle)
                    crop = imageC[int(newY-h/2):int(newY+h/2),
                                  int(newX-w/2):int(newX+w/2)]
                    facesFound.append(crop)

            except:
                continue

    return facesFound


def __raw_face_landmarks__(face_image, pose_predictor_5_point):
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
    raw_landmarks = __raw_face_landmarks__(face_image, pose_predictor_5_point)
    encoding = face_encoder.compute_face_descriptor(
        face_image, raw_landmarks, num_jitters)
    return encoding

def predictClass(encoding, knnClasifier):
    """
    Returns an array of the predicted Student and its probabilty

    :param img: An image (as a numpy array)
    :savePath str: An string of weather you should store the images or not 
    :return: A list of tuples of found face locations in css (top, right, bottom, left) order
    """
    knn = knnClasifier[0]
    names = knnClasifier[1]

    encoding = np.array(encoding).reshape(1, -1)
    neighDis, neighIndx = knn.kneighbors(encoding,5,return_distance=True)
    neighDis = neighDis[0]
    neighIndx = neighIndx[0]
    neigClasses = []
    for i, j in enumerate(neighIndx):
        neighDis[i] = neighDis[i]*10
        neigClasses.append(names[int(j)])
    
    return knn_weighted_vote(neighDis, neigClasses)

def knn_weighted_vote(distances, predictedClasses, threshold=1):
    """
    Takes in the distances and predicted classes from a k-nearest neighbors model, groups the predicted
    classes by frequency, weights the frequency by distance, and returns the predicted class if the
    highest weighted frequency is above a given threshold.
    
    Args:
        distances (numpy.ndarray): Array of distances.
        predictedClasses (list): List of predicted classes.
        threshold (float): Threshold for the highest weighted frequency.
        
    Returns:
        str: Predicted class if the highest weighted frequency is above the given threshold, otherwise None.
    """
    # Find the unique predicted classes and their frequencies
    class_counts = Counter(predictedClasses)
    
    # Calculate the weighted frequency of each predicted class
    weighted_counts = {}
    for cls in class_counts:
        indices = [i for i, c in enumerate(predictedClasses) if c == cls]
        distances_to_cls = distances[indices]
        weights = 1 / (distances_to_cls + 1e-8)
        weighted_count = sum(weights)
        weighted_counts[cls] = weighted_count
    
    # Find the predicted class with the highest weighted frequency
    max_weighted_count = max(weighted_counts.values())
    if max_weighted_count >= threshold:
        predicted_class = max(weighted_counts, key=weighted_counts.get)
        return [predicted_class, max_weighted_count] 
    else:
        return None