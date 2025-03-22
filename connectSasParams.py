from datetime import datetime as dt
import saspy
import sys
import os
import json
import subprocess


class ExtractDataSas():
    path = "/data/axiom/Default_py/"
    fileTemplate = "maca_prueba.txt"
    inputJson = {}
    dataSourceName = None
    ODATE = None
    isQuery = None
    query = ""

    def __init__(self, parameters):
        self.parameters = parameters
        self.validateArgs()        
        self.readJsonInput()
        self.defineSource()
        self.createSessionSas()

    def readJsonInput(self):
        file_path = self.path + "connectSasParams.json"
        if os.path.exists(file_path):
            self.inputJson = json.load(open(file_path, "r"))
        else:
            self.createJsonFileFromTemplateSasParam()

    def createJsonFileFromTemplateSasParam(self):
        datajson = '{"data" : {'
        datajson += "\n\t\"{}\": {{".format(self.dataSourceName)
        manipulated_line = ""
        with open(self.path + self.fileTemplate , "r") as file:
            for line in file:
                if self.dataSourceName in line: 
                    paramList= [v.strip() for v in line.strip().split("_xx_")]
                    datajson += """\n\t\t\"connect\": {{
                                                \"host\": \"{host}\",
                                                \"port\": \"{port}\",
                                                \"sas_usr\": \"{sas_usr}\",
                                                \"sas_pwd\": \"{sas_pwd}\"                                                
                                            }},""".format(host=paramList[3], port= paramList[4], sas_usr= paramList[9], sas_pwd= paramList[10])
                    datajson += """\n\t\t\"source\": {{
                                                \"table\": \"{table}\",
                                                \"fileName\": \"{fileName}\",
                                                \"query\": {query},
                                                \"esquema\": \"{esquema}\",
                                                \"path\": \"{path}\",
                                                \"periodicity\": \"{periodicity}\",
                                                \"outputFileName\": \"{outputFileName}\",
                                                \"separator\": \"{separator}\",
                                                \"header\": {header}
                                            }},""".format(table=paramList[7],fileName= paramList[12],query= "false" if "NO" == paramList[15] else "true",                                      
                                                            esquema= paramList[5], path= paramList[6], periodicity= "D" if "yyyymmdd" in paramList[7] else "M",  
                                                            outputFileName= paramList[11], separator= paramList[13], header= "false" if "NO" == paramList[14] else "true")
                    datajson += """\n\t\t\"filter\": [{{
                                                \"filter1\": \"{filter1}\"                                                                                               
                                            }}],""".format(filter1=paramList[8],                
                                               )
                    datajson += """\n\t\t\"select\": [{{
                                                \"select1\": [\"{select1}\"]                                                                                               
                                            }}]""".format(select1=paramList[16],                
                                               )
        
        datajson += "\n\t }\n }\n}"
        self.inputJson = json.loads(datajson)
                
    def validateArgs(self):
        print("self.parameters",self.parameters)
        if len(self.parameters) not in [3,4]:

            print("""Error en la cantidad de argumentos se ingresaron {0}
            Se requiere de almenos 2 argumentos para la ejecucion correcta del extractor SAS
            1. Fuente de datos
            2. ODATE
            4. Query es opcional # viene de where condition en tu tabla SASParams

            Ejemplo:::::  python connectSasParams.py HRC_TM_GARANTIAS 20241223 query:::::::
            query es opcional
            """.format(len(self.parameters)))
            sys.exit()
        self.dataSourceName = self.parameters[1]
        self.ODATE = self.parameters[2]
        self.isQuery = self.parameters[3] if len(self.parameters) == 4 else None

    def validateOdate(self):
        if self.SRC["periodicity"] == "M" and "yyyyMM" in self.SRC["table"]:
            self.SRC["table"] = self.SRC["table"].replace("yyyyMM", self.ODATE[0:6])
        elif self.SRC["periodicity"] == "D" and "yyyyMMdd" in self.SRC["table"]:
            self.SRC["table"] = self.SRC["table"].replace("yyyyMMdd", self.ODATE)

    def asignTablesQuery(self,query):
        if self.SRC["periodicity"] == "M" :
            self.query=' \n'.join(query["query1"]).replace("yyyyMM", self.ODATE[0:6])
        elif self.SRC["periodicity"] == "D":
            self.query=' \n'.join(query["query1"]).replace("yyyyMMdd", self.ODATE)                                                           
    
    def defineSource(self):
        where = ""
        keep = ""
        for key, value in self.inputJson["data"].items():
            if self.parameters[1] == key:
                
                self.SRC = value["source"]
                self.SRC['fileNameSRC'] = self.SRC['fileName'] +'_'+self.ODATE + '.txt'
                self.validateOdate()
                
                for filtro in value["filter"]:
                    if "filter1" in filtro:
                        where = "'where': '{}'".format(filtro["filter1"])
                for select in value["select"]:
                    if "select1" in select and select["select1"] != '':
                        keep = "'keep': {}".format(select["select1"])
                if self.SRC["query"]:
                    for query in value["query"]:
                        if "query1" in query and query["query1"] != '':
                            self.asignTablesQuery(query)
        self.dsopts = "{"+ where +","+ keep +"}"
        
    def createSessionSas(self):
        dir_config = self.path+"sascfg_psn.py"
        conn = self.inputJson["data"][self.dataSourceName]["connect"]
        self.sas = saspy.SASsession(cfgname="iomlinux", cfgfile=dir_config,iomhost=conn["host"], iomport=conn["port"], omruser=conn["sas_usr"], omrpw="S45j4Npr3.")
        
    def loadLibName(self):
        if self.SRC["esquema"] in self.sas.assigned_librefs():
            print("El esquema ya esta cargado")
        else:
            self.sas.saslib(self.SRC["esquema"],path=self.SRC["path"])
            print("El esquema se ha cargado")        
        print(self.sas.assigned_librefs())
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
        self.sas.submitLOG(code=f"""PROC SQL;
                                    CREATE TABLE WORK.TEMP_{self.SRC["fileName"]} AS
                                        {self.query};
                                    QUIT;""")
        self.reviewErrorSAS()
    
    def createTxtSAS(self):
        self.sas.write_csv(self.sas.workpath + self.SRC["fileNameSRC"],
                            "TEMP_"+self.SRC["fileName"],
                            "WORK",                            
                            opts= {'delimiter' : self.SRC["separator"],  'putnames'  : self.SRC["header"] }
                        )
        self.reviewErrorSAS()
    
    def downTxtSAS(self):
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
        if not self.SRC["query"]:                  
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

    def runProcess(self):
        self.loadLibName()
        self.getPreviewData()
        self.executeQuery()
        
def main(args):
    ExtractDataSas(args).runProcess()

if __name__ == "__main__":
    # ejemplo de ejecucion \'Program Files'\Python311\python.exe connectSasParams.py HRC_TM_GARANTIAS 20241223 query1
    # parameter query1 its optional
    main(sys.argv)
