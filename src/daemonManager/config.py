from json import loads
from configparser import ConfigParser
from distutils.dir_util import copy_tree
from socket import gethostbyname, gethostname
from shutil import copyfile
import zipfile
import io
import os
import requests


def configServer(serverIP, configDir, dataDir):
    setupFiles(configDir, dataDir)
    configur = ConfigParser()
    configur.read(dataDir+'/config.ini')

    CLASSROOMNUM = configur.getint('CONFIG', 'numClass')
    CLASSROOMNAME = configur.get('CONFIG', 'nameClass')

    KNN = configur.getint('VERSION', 'knn')
    NAMES = configur.getint('VERSION', 'names')

    IPADDRESS = gethostbyname(gethostname()+".local")

    data = {
        "classNumber": CLASSROOMNUM,
        "className": CLASSROOMNAME,
        "ipClassroom": IPADDRESS,
        "idClassroom": None
    }

    versions = {
        "classNumber": CLASSROOMNUM,
        "className": CLASSROOMNAME,
        'Knn': KNN,
        'Names': NAMES,
    }

    if (configur.has_option('CONFIG', 'idClassroom')):
        idClassroom = configur.getint('CONFIG', 'idClassroom')
        data["idClassroom"] = idClassroom
        response = requests.get(
            'http://'+serverIP+"/classroom/", json=data)
        print('Update ip')
    else:
        response = requests.get(
            'http://'+serverIP+"/classroom/", json=data)
        print('Setting new id')
        res = loads(response.content.decode())
        idClassroom = str(res['idClassroom'])
        configur.set('CONFIG', 'idClassroom', idClassroom)

    upResponse = requests.get(
        'http://'+serverIP+"/recog/update", json=versions)

    if upResponse.status_code == 200:
        responseData = upResponse.content
        update = upResponse.headers.get('update')
        # Check if the bytes are not empty
        print("Updating Models")
        if responseData and update:
            # Save the pickled objects to files
            zip_data = io.BytesIO(responseData)
            file_dict = {}
            with zipfile.ZipFile(zip_data, mode='r') as zip_file:
                for file_info in zip_file.infolist():
                    with zip_file.open(file_info) as file:
                        file_dict[file_info.filename] = file.read()

            if file_dict['knn']:
                knn_new_version = upResponse.headers.get('knnNewVersion')
                configur.set('VERSION', 'knn', knn_new_version)
                with open(dataDir+'/models/knnPickleFile.pickle', 'wb') as f:
                    f.write(file_dict['knn'])
            if file_dict['names']:
                names_new_version = upResponse.headers.get('namesNewVersion')
                configur.set('VERSION', 'names', names_new_version)
                with open(dataDir+'/models/namesFile.pickle', 'wb') as f:
                    f.write(file_dict['names'])
        else:
            print('No data was received from the server.')

    else:
        print(f'No Problem {response.status_code}.')

    with open(dataDir+'/config.ini', 'w') as inifile:
        configur.write(inifile)
    return idClassroom


def setupFiles(configDir, dataDir):
    if not (os.path.exists(dataDir+'/config.ini')):
        print(dataDir)
        copyfile(configDir+'/config.ini', dataDir+'/config.ini')
        copy_tree(configDir+'/models/', dataDir+'/models/')
