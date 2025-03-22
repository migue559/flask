# conectSas.py
# Importacion de los modulos de manejo de la plataforma con los cuales se hara el proceso
# de manipulacion y generacion de fuentes para CV10 desde SAS
from datetime import datetime as dt
from collections import namedtuple
import saspy
import platform
import pandas as data
import sys
import os
import json
import subprocess
# Proceso de Validacion de argumentos para el uso del esquema y tabla del ambiente SAS
# En caso de que no se envie ningun parametro el modulo seleccionara la tabla CARS del esquema SASHELP


class ExtractDataSas():
    inputJson = {}
    SRC = {}
    dsopts = {}
    query = ""

    def __init__(self, parameters):
        self.ODATE = parameters[4]
        self.parameters = parameters
        self.readJsonInput()
        self.validateArgs()
        self.defineSource()
        self.createSessionSas()


    def readJsonInput(self):
        #self.inputJson = json.load(open("conectSas.json", "r"))
        self.inputJson = json.load(open("/data/axiom/Default_py/conectSas.json", "r"))


    def validateArgs(self):
        if len(self.parameters) not in [5,6]:

            print("""Error en la cantidad de argumentos se ingresaron {0}
            Se requiere de 2 argumentos para la ejecucion correcta del extractor SAS
            1. Fuente de datos
            2. Filtro de la tabla a extraer

            Nota estos parametros se cargan en el archivo conectSas.json

            Ejemplo:::::  python conectSas.py sourceSas2 filter1 select1 20241223 :::::::
            """.format(len(self.parameters)))
            sys.exit()

    def validateSRC_dsopts(self):
        if len(self.SRC) == 0 or not self.dsopts:
            print("""Error en la definicion de la fuente o filtro
            Los argumentos incovados no existe favor de verificar la informacion con el archivo conectSas.json

            argumentos utilizados: {0} y {1}

            disponibles en el archivo conectSas.json

            {2}

            """.format(self.parameters[1], self.parameters[2],"222"))
            #""".format(self.parameters[1], self.parameters[2], json.dumps(self.inputJson["data"], indent=2)))
            sys.exit()

    def validateOdate(self):
        if self.SRC["periodicity"] == "M" and "yyyyMM" in self.SRC["table"]:
            self.SRC["table"] = self.SRC["table"].replace("yyyyMM", self.ODATE[0:6])
        elif self.SRC["periodicity"] == "D" and "yyyyMMdd" in self.SRC["table"]:
            self.SRC["table"] = self.SRC["table"].replace("yyyyMMdd", self.ODATE)
        print("#######", self.SRC)

    def asignTablesQuery(self,query):
        if self.SRC["periodicity"] == "M" :
            self.query=' \n'.join(query[self.parameters[5]]).replace("yyyyMM", self.ODATE[0:6])
        elif self.SRC["periodicity"] == "D":
            self.query=' \n'.join(query[self.parameters[5]]).replace("yyyyMMdd", self.ODATE)
        print(self.query)

    def validateQuery(self):
        if self.SRC["query"]:
            self.query = self.SRC["query"]

        pass

    def defineSource(self):
        where = ""
        keep = ""
        for key, value in self.inputJson["data"].items():
            if self.parameters[1] == key:

                self.SRC = value["source"]
                self.SRC['fileNameSRC'] = self.SRC['fileName'] +'_'+self.ODATE + '.txt'
                if self.SRC['table'] != 'CARS':
                    self.validateOdate()
                #self.SRC = value["source"]
                for filtro in value["filter"]:
                    #print(self.parameters[2],filtro, value["select"])
                    if self.parameters[2]  in filtro:
                        where = "'where': '{}'".format(filtro[self.parameters[2]])
                for select in value["select"]:
                    if self.parameters[3] in select and select[self.parameters[3]] != '':
                        keep = "'keep': {}".format(select[self.parameters[3]])
                if self.SRC["query"]:
                    for query in value["query"]:
                        if self.parameters[5] in query and query[self.parameters[5]] != '':
                            self.asignTablesQuery(query)

        self.dsopts = "{"+ where +","+ keep +"}"
        self.validateSRC_dsopts()



    def createSessionSas(self):
        # Directorio con la configuración de Saspy

        dir_config = "/data/axiom/Default_py/sascfg_personal.py"
        #dir_config = f"{os.getcwd()}\\sascfg_personal.py"
        # Instancia de Saspy, solicitará user y password
        #self.sas = saspy.SASsession(cfgname="winiomlinux", cfgfile=dir_config)
        self.sas = saspy.SASsession(cfgname="iomlinux", cfgfile=dir_config)


    def loadLibName(self):
        # Extraccion de la data y generacion del archivo fuente que sera usado en el Data Load de Cv10
        if self.SRC["esquema"] in self.sas.assigned_librefs():
            print("El esquema ya esta cargado")
        else:
            self.sas.saslib(self.SRC["esquema"],path=self.SRC["path"])
            print("El esquema se ha cargado")
            #libRes = self.sas.saslog()
            #print("**********************************")
            #print(libRes)


        assigned_librefs = self.sas.assigned_librefs() # Check all assigned libraries
        print(assigned_librefs)
        print(self.sas.list_tables(self.SRC["esquema"]))

    def closeSessionSas(self):
        self.sas.endsas()

    def getPreviewData(self):
        self.dataP = self.sas.sasdata(self.SRC["table"], self.SRC["esquema"])
        print(self.dataP.head())

    def reviewErrorSAS(self):
        if "ERROR" in self.sas.lastlog():
            print("""Error en la ejecucion de la query
                    el error es el siguiente: {0}
                    """.format(self.sas.lastlog()))
            sys.exit("error message: \n", self.sas.lastlog())

    def createTempSAS(self):
        self.sas.submitLOG(code=f"""
                            PROC SQL;
                                    CREATE TABLE WORK.TEMP_{self.SRC["fileName"]} AS
                                        {self.query}
                            ;
                            QUIT;
                            """)
        self.reviewErrorSAS()

    def createTxtSAS(self):
        self.sas.write_csv(self.sas.workpath + self.SRC["fileNameSRC"],
                            "TEMP_"+self.SRC["fileName"],
                            "WORK",
                            opts= {'delimiter' : self.SRC["separator"],  'putnames'  : self.SRC["header"] }
                        )
        self.reviewErrorSAS()

    def downTxtSAS(self):
        #pathTemp = f"{os.getcwd()}\\" + self.SRC["fileNameSRC"]
        pathTemp =  self.SRC["outputFileName"]
        pathTempSas = self.sas.workpath + self.SRC["fileNameSRC"]

        res = self.sas.download(pathTemp , pathTempSas)
        self.reviewErrorSAS()
        print(res['LOG'])
        print("Documento Descargado... ")
        print("Inicio eliminacion de temporal")
        res_del = self.sas.file_delete(pathTempSas)
        print(res_del)
        self.reviewErrorSAS()

    def dropTmpSAS(self):
        self.sas.submitLOG(code=f""" PROC SQL ;    DROP TABLE  WORK.TEMP_{self.SRC["fileName"]}; QUIT; """)
        self.reviewErrorSAS()





    def executeQuery(self):
        if self.SRC["query"]:
            self.createTempSAS()
            self.createTxtSAS()
            self.downTxtSAS()
            self.dropTmpSAS()

        else:
            self.query+="SELECT "
            self.query+=" {0} ".format( ','.join( eval(self.dsopts)["keep"]) )
            self.query+=" FROM {0}.{1}".format(self.SRC["esquema"],self.SRC["table"])
            if eval(self.dsopts)["where"] != "":
                self.query+=" WHERE {0} ".format(eval(self.dsopts)["where"])
            print("Query a ejecutar: ", self.query)

            self.createTempSAS()
            self.createTxtSAS()
            self.downTxtSAS()
            self.dropTmpSAS()

        self.closeSessionSas()
        self.changeEncodingFile()
        sys.exit()


    def generateDataSasServer(self):
        print(self.sas.workpath + self.SRC["fileNameSRC"],
                        self.SRC["table"] ,
                        self.SRC["esquema"],
                        self.dsopts,
                        {'delimiter' : '|',  'putnames'  : False }
                        )
        if not self.executeQuery():
            print("No se ejecuto la query")

        try:
            self.sas.write_csv(self.sas.workpath + self.SRC["fileNameSRC"],
                            self.SRC["table"] ,
                            self.SRC["esquema"],
                            dsopts= eval(self.dsopts),
                            opts= eval("{'delimiter' : '|',  'putnames'  : True }")
                        )
            self.reviewErrorSAS()
            return True
        except Exception as e:
            print("""Error en la generacion de la data  --generateDataSasServer --

            El error producido es el siguiente: {0}

            """.format(e))
            sys.exit()


    def changeEncodingFile(self):
        print("Inicia recodificacion UTF-8")
        inputFile = self.SRC["outputFileName"] + self.SRC["fileNameSRC"]
        outputFile = self.SRC["outputFileName"] + self.SRC["fileNameSRC"] + "utf"
        cmd1 = f"iconv -f ISO-8859-1 -t UTF-8//TRANSLIT {inputFile} -o {outputFile}"
        cmd2 = f"rm {inputFile}"
        cmd3 = f"mv {outputFile} {inputFile}"
        p1 = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = p1.wait()
        p2 = subprocess.Popen(cmd2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = p2.wait()
        p3 = subprocess.Popen(cmd3, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = p3.wait()

        return True

    def runProcess(self):
        print("runProcess")
        self.loadLibName()
        self.getPreviewData()
        if not self.executeQuery():
            print("No se ejecuto la query")
        self.reviewErrorSAS()
        self.closeSessionSas()
        self.changeEncodingFile()
        return 0

def main(args):
    ExtractDataSas(args).runProcess()

if __name__ == "__main__":
    # ejemplo de ejecucion \'Program Files'\Python311\python.exe conectSas.py sourceSas1 filter1 select1 20241223 query1
    # parameter query1 its optional
    args = sys.argv
    main(args)
