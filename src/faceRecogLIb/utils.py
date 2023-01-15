import numpy as np
import math
from cv2 import getRotationMatrix2D,warpAffine,INTER_LINEAR

def rotate_image(image, angle):
  image_center = tuple(np.array(image.shape[1::-1]) / 2)
  rot_mat = getRotationMatrix2D(image_center, angle, 1.0)
  result = warpAffine(image, rot_mat, image.shape[1::-1], flags=INTER_LINEAR)
  return result
  
def getAngle(lefEye,rightEye):
    catAd = rightEye[0] - lefEye[0]
    catOp = rightEye[1] - lefEye[1]
    angle =math.atan(catOp/catAd)
    if angle > 0.2618 or angle < -0.2618:
        return angle
    else:
        return 0

def getNewLocations(centerCrop,centerImage,angle):
  x = centerCrop[0]
  y = centerCrop[1]
  p = centerImage[0]
  q = centerImage[1]
  θ = angle
  newX = int((x-p)*math.cos(θ)-(y-q)*math.sin(θ)+p)
  newY = int((x-p)*math.sin(θ)+(y-q)*math.cos(θ)+q)
  return newX,newY