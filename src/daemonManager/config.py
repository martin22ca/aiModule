from json import loads
from configparser import ConfigParser
from socket import gethostbyname,gethostname
import requests

def configServer(serverIP,iniPath):
    configur = ConfigParser()
    configur.read(iniPath)

    CLASSROOMNUM = configur.getint('CONFIG','numClass')
    CLASSROOMNAME = configur.get('CONFIG','nameClass')

    IPADDRESS = gethostbyname(gethostname()+".local")

    data ={
        "classNumber": CLASSROOMNUM,
        "className": CLASSROOMNAME,
        "ipClassroom": IPADDRESS,
        "idClassroom": None
    } 

    if (configur.has_option('CONFIG','idClassroom')):
        idClassroom =  configur.getint('CONFIG','idClassroom')
        data["idClassroom"] = idClassroom
        response = requests.get('http://'+serverIP+":5000/classroom/" , json=data)
        print('Update ip')
    else:
        response = requests.get('http://'+serverIP+":5000/classroom/" , json=data)
        print('Setting new id')
        res = loads(response.content.decode())
        idClassroom = str(res['idClassroom'])

        configur.set('CONFIG','idClassroom',idClassroom)

        with open(iniPath, 'w') as inifile:
            configur.write(inifile)

    return idClassroom
