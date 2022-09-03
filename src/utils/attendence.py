import cv2
import os
import requests
from utils import recog
from datetime import date, timedelta


def attendence(id_class):
    pics_dir = "src/camPhotos/"
    pics = os.listdir(pics_dir)
    present = []
    mod = str(id_class)

    for i in pics:
        img = cv2.imread(pics_dir+i)
        result = recog.predict(img, model_path="src/cache_models/" +
                               mod+"_model.clf", distance_threshold=0.7)
        if result:
            pred = result[0][0]
            if pred not in present:
                present.append(pred)
    return present


def roll_call(id_emp, id_clas):
    today = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))

    day = {
        "today": today,
        "tomorrow": tomorrow
    }

    #chechk if roll call found
    r = requests.get('http://localhost:9023/api/roll', json=day)

    # No roll call found today
    if r.status_code == 404:
        start = today + ' 07:25:00'

        roll = {
            "id_employee": id_emp,
            "id_classroom": id_clas,
            "start_class": start
        }
        # create roll_call_default
        requests.post('http://localhost:9023/api/roll', json=roll)

        r = requests.get('http://localhost:9023/api/roll', json=day)

    return r.json()['id']


def get_attendece(id_employee,id_classroom,id_class):
    id_roll = roll_call(id_employee, id_classroom)
    present = attendence(id_class)

    stu = {
        "id_class": id_class,
        "id_roll_call":id_roll,
        "present": present
    }

    post = requests.post('http://localhost:9023/api/att', json=stu)
    return post
    
