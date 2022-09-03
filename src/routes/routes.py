from __main__ import app

import os
import json
import requests
from klein import Klein
from dotenv import load_dotenv
from utils.attendence import get_attendece

load_dotenv()
id_classroom = os.getenv('CLASSROOM')

@app.route('/',methods=['GET'])
def pg_root(request):
    return 'I am the root page!'

@app.route('/class', methods=['POST'])
def do_post(request):
    content = json.loads(request.content.read())
    response = json.dumps(dict(content), indent=4)

    id_class = content['id_class']
    id_employee = content['id_employee']

    res = get_attendece(id_employee, id_classroom, id_class)

    if res.status_code == 200:
        return "Registered Attendence"
    else:
        return str(res.status_code)