from math import atan, cos, sin
from getmac import get_mac_address as gma
from numpy import ndarray, array, round, floor, ceil
from cv2 import getRotationMatrix2D, warpAffine, resize, copyMakeBorder, INTER_LINEAR, INTER_AREA, INTER_CUBIC, BORDER_CONSTANT


def rotate_image(image, angle):
    image_center = tuple(array(image.shape[1::-1]) / 2)
    rot_mat = getRotationMatrix2D(image_center, angle, 1.0)
    result = warpAffine(image, rot_mat, image.shape[1::-1], flags=INTER_LINEAR)
    return result


def getAngle(lefEye, rightEye):
    catAd = rightEye[0] - lefEye[0]
    catOp = rightEye[1] - lefEye[1]
    angle = atan(catOp/catAd)
    if angle > 0.2618 or angle < -0.2618:
        return angle
    else:
        return 0


def getNewLocations(centerCrop, centerImage, angle):
    x = centerCrop[0]
    y = centerCrop[1]
    p = centerImage[0]
    q = centerImage[1]
    θ = angle
    newX = int((x-p)*cos(θ)-(y-q)*sin(θ)+p)
    newY = int((x-p)*sin(θ)+(y-q)*cos(θ)+q)
    return newX, newY


def resizeAndPad(img, size, padColor=0):
    h, w = img.shape[:2]
    sh, sw = size

    # interpolation method
    if h > sh or w > sw:  # shrinking image
        interp = INTER_AREA

    else:  # stretching image
        interp = INTER_CUBIC

    # aspect ratio of image
    aspect = float(w)/h
    saspect = float(sw)/sh

    if (saspect >= aspect) or ((saspect == 1) and (aspect <= 1)):  # new horizontal image
        new_h = sh
        new_w = round(new_h * aspect).astype(int)
        pad_horz = float(sw - new_w) / 2
        pad_left, pad_right = floor(pad_horz).astype(
            int), ceil(pad_horz).astype(int)
        pad_top, pad_bot = 0, 0

    elif (saspect < aspect) or ((saspect == 1) and (aspect >= 1)):  # new vertical image
        new_w = sw
        new_h = round(float(new_w) / aspect).astype(int)
        pad_vert = float(sh - new_h) / 2
        pad_top, pad_bot = floor(pad_vert).astype(
            int), ceil(pad_vert).astype(int)
        pad_left, pad_right = 0, 0

    # set pad color
    # color image but only one color provided
    if len(img.shape) == 3 and not isinstance(padColor, (list, tuple, ndarray)):
        padColor = [padColor]*3

    # scale and pad
    scaled_img = resize(img, (new_w, new_h), interpolation=interp)
    scaled_img = copyMakeBorder(
        scaled_img, pad_top, pad_bot, pad_left, pad_right, borderType=BORDER_CONSTANT, value=padColor)

    return scaled_img


def getMacAddr():
    return str(gma())
