from json import loads
from configparser import ConfigParser
from distutils.dir_util import copy_tree
from socket import gethostbyname, gethostname
from shutil import copyfile
import zipfile
import io
import os
import requests


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
            print(dataDir)
            copyfile(configDir+'/config.ini', dataDir+'/config.ini')
            copy_tree(configDir+'/models/', dataDir+'/models/')
        return None

    def configServer(self):
        print('*- Buscando servidor ....')
        ipServer = None
        if (self.configur.has_option('CONFIG', 'ipserver')):
            ipServer = self.configur.get('CONFIG', 'ipserver') + ':5000'
        else:
            print('*- No hay Ip Configurado')
            return None

        idClassroom = self.configId(ipServer)
        if idClassroom == None:
            return None

        self.updateModels(ipServer)

        with open(self.dataDir+'/config.ini', 'w') as inifile:
            self.configur.write(inifile)

        return idClassroom, ipServer, self.configur.getint('CONFIG', 'debug'), self.configur.getint('CAM', 'rotation') 

    def configId(self, ipServer):
        try:
            if (self.configur.has_option('CONFIG', 'idClassroom')):
                idClassroom = self.configur.getint('CONFIG', 'idClassroom')
                self.data["idClassroom"] = idClassroom
                response = requests.get(
                    'http://'+ipServer+'/classroom/', json=self.data, timeout=2)
                return idClassroom
            else:
                print('*- Creando nuevo Curso')
                response = requests.get(
                    'http://'+ipServer+'/classroom/', json=self.data, timeout=2)
                res = loads(response.content.decode())
                idClassroom = str(res['idClassroom'])
                self.configur.set('CONFIG', 'idClassroom', idClassroom)
                return idClassroom
        except:
            print('*- Timeout del servidor')
            return None

    def updateModels(self, ipServer):
        upResponse = requests.get(
            'http://'+ipServer+"/recog/update", json=self.data)
        if upResponse.status_code == 200:
            responseData = upResponse.content
            update = upResponse.headers.get('update')
            print("*- Actualizando Modelos")
            if responseData and update:

                zip_data = io.BytesIO(responseData)
                file_dict = {}
                with zipfile.ZipFile(zip_data, mode='r') as zip_file:
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
