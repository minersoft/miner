import json
import sys
from m.common import GeneratorBase

class iJson(GeneratorBase):
    """Json stream reads object(s) from json file,
    Multiple objects are generated if json represents a list"""
    def __init__(self, fileHandler):
        GeneratorBase.__init__(self)
        self.myFileHandler = fileHandler
    def __iter__(self):
        try:
            obj = json.load(self.myFileHandler)
            if isinstance(obj, list):
                for el in obj:
                    yield (el, )
            else:
                yield (obj, )
        except:
            pass
    def close(self):
        self.myFileHandler.close()

    def getVariableNames(self):
        return ["obj"]

class oJson(object):
    def __init__(self, fileName, variableNames, indent=4):
        if fileName == "stdout":
            self.filehandle = sys.stdout
        else:
            self.filehandle = open(fileName, "wb")
        self.variableNames = variableNames
        print >>self.filehandle, "["
        self.isFirst = True
        self.indent = indent
    
    def save(self, record):
        r = {}
        for i, v in enumerate(self.variableNames):
            r[v] = record[i]
        if self.isFirst:
            self.isFirst = False
        else:
            print >>self.filehandle, ","
        json.dump(r, self.filehandle, indent=self.indent)
    def close(self):
        print >>self.filehandle, "]"
        if self.filehandle is not sys.stdout:
            self.filehandle.close()
