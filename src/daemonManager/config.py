from requests.exceptions import RequestException
from socket import gethostbyname, gethostname
from distutils.dir_util import copy_tree
from configparser import ConfigParser
from zipfile import ZipFile
from shutil import copyfile
from json import loads
from io import BytesIO
from time import sleep

import requests
import os


class serverSetup():
    def __init__(self, configDir, dataDir) -> None:
        self.dataDir = dataDir
        self.setupFiles(configDir, self.dataDir)

        self.configur = ConfigParser()
        self.configur.read(self.dataDir + '/config.ini')

        self.data = {
            'classNumber': self.configur.getint('CONFIG', 'numClass'),
            'className': self.configur.get('CONFIG', 'nameClass'),
            'ipClassroom': gethostbyname(gethostname()+".local"),
            'idClassroom': None,
            'Knn': self.configur.getint('VERSION', 'knn'),
            'Names': self.configur.getint('VERSION', 'names'),
        }

        return None

    def setupFiles(self, configDir, dataDir):
        print('*- Archivos Localizados en: ', dataDir)
        if not (os.path.exists(dataDir+'/config.ini')):
            os.makedirs(dataDir, exist_ok=True)
            os.mkdir(dataDir+'/models/')
            copy_tree(configDir+'/models/', dataDir+'/models/')
            copyfile(configDir+'/config.ini', dataDir+'/config.ini')
        return None

    def configServer(self):
        ipServer = None
        if (self.configur.has_option('CONFIG', 'ipserver')):
            ipServer = self.configur.get('CONFIG', 'ipserver') + ':3001'
            print('*- Buscando servidor en ' + ipServer + ' ....')
            sleep(2)
        else:
            print('*- No hay Ip Configurado')
            return None

        idClassroom = self.configId(ipServer)
        if idClassroom == None:
            return None

        self.updateModels(ipServer)

        with open(self.dataDir+'/config.ini', 'w') as inifile:
            self.configur.write(inifile)

        return idClassroom, ipServer, self.configur.getint('CAM', 'visible'), self.configur.getint('CAM', 'rotation')

    def configId(self, ipServer):
        try:
            if (self.configur.has_option('CONFIG', 'idClassroom')):
                idClassroom = self.configur.getint('CONFIG', 'idClassroom')
                self.data["idClassroom"] = idClassroom
                response = self.retryableGetRequest('http://'+ipServer+'/modules/', self.data)
                if response == None: return None
                return idClassroom
            else:
                requestCreate = 'http://'+ipServer+'/modules/newModule'
                sleep(2)
                response = self.retryableGetRequest(requestCreate, self.data)
                if response == None: return None
                res = loads(response.content.decode())
                idClassroom = str(res['idClassroom'])
                self.configur.set('CONFIG', 'idClassroom', idClassroom)
                return idClassroom
        except Exception as e:
            print("*- " + str(e))
            return None

    def updateModels(self, ipServer):
        upResponse = self.retryableGetRequest(
            'http://'+ipServer+'/recog/update', self.data)
        if upResponse.status_code == 200:
            responseData = upResponse.content
            update = upResponse.headers.get('update')
            print("*- Actualizando Modelos")
            sleep(2)
            if responseData and update:

                zip_data = BytesIO(responseData)
                file_dict = {}
                with ZipFile(zip_data, mode='r') as zip_file:
                    for file_info in zip_file.infolist():
                        with zip_file.open(file_info) as file:
                            file_dict[file_info.filename] = file.read()

                if file_dict['knn']:
                    knn_new_version = upResponse.headers.get('knnNewVersion')
                    self.configur.set('VERSION', 'knn', knn_new_version)
                    with open(self.dataDir + '/models/knnPickleFile.pickle', 'wb') as f:
                        f.write(file_dict['knn'])
                if file_dict['names']:
                    names_new_version = upResponse.headers.get(
                        'namesNewVersion')
                    self.configur.set('VERSION', 'names', names_new_version)
                    with open(self.dataDir + '/models/namesFile.pickle', 'wb') as f:
                        f.write(file_dict['names'])
            else:
                print('*- No hay modelos Nuevos')
        else:
            print(f'Problem {upResponse.status_code}.')

    def retryableGetRequest(self, url, data, timeout=5, retries=5):
        for retry in range(retries):
            try:
                response = requests.get(url, json=data, timeout=timeout)
                response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
                return response
            except RequestException as e:
                print(f"*- Intento {retry + 1} fallido. Reintentando")
                sleep(1)
                if retry >= retries - 1:
                    print("*- No se puedo conectar con el servidor.")
                    break
