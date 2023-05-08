from json import loads
from configparser import ConfigParser
from socket import gethostbyname, gethostname
import zipfile
import io
import requests

def configServer(serverIP, iniPath):
    configur = ConfigParser()
    configur.read(iniPath)

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
        'Knn': KNN,
        'Names': NAMES,
    }

    if (configur.has_option('CONFIG', 'idClassroom')):
        idClassroom = configur.getint('CONFIG', 'idClassroom')
        data["idClassroom"] = idClassroom
        response = requests.get(
            'http://'+serverIP+":5000/classroom/", json=data)
        print('Update ip')
    else:
        response = requests.get(
            'http://'+serverIP+":5000/classroom/", json=data)
        print('Setting new id')
        res = loads(response.content.decode())
        idClassroom = str(res['idClassroom'])

        configur.set('CONFIG', 'idClassroom', idClassroom)

    upResponse = requests.get(
        'http://'+serverIP+":5000/recog/update", json=versions)
    if upResponse.status_code == 200:

        knn_new_version = upResponse.headers.get('knnNewVersion')
        names_new_version = upResponse.headers.get('namesNewVersion')
        configur.set('VERSION', 'knn', knn_new_version)
        configur.set('VERSION', 'names', names_new_version)

        responseData = upResponse.content
        # Check if the bytes are not empty
        if responseData:
            # Save the pickled objects to files
            zip_data = io.BytesIO(responseData)
            file_dict = {}
            with zipfile.ZipFile(zip_data, mode='r') as zip_file:
                for file_info in zip_file.infolist():
                    with zip_file.open(file_info) as file:
                        file_dict[file_info.filename] = file.read()

            if file_dict['knn']:
                with open('src/recogLib/models/knnPickleFile.pickle', 'wb') as f:
                    f.write(file_dict['knn'])
            if file_dict['names']:
                with open('src/recogLib/models/namesFile.pickle', 'wb') as f:
                    f.write(file_dict['names'])
        else:
            print('No data was received from the server.')

    else:
        print(f'Request failed with status code {response.status_code}.')

    with open(iniPath, 'w') as inifile:
        configur.write(inifile)
    return idClassroom
