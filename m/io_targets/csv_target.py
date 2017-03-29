from m.common import GeneratorBase
import os.path
import csv
import sys

class iCSV(GeneratorBase):
    def __init__(self, fileHandler, vars=None, delimiter=","):
        GeneratorBase.__init__(self)
        self.myFileHandler = fileHandler
        self.reader = csv.reader(self.myFileHandler, delimiter=delimiter)
        if vars:
            self.myVars = vars.rstrip().split(",")
        else:
            self.myVars = self.reader.next()
    def getVariableNames(self):
        return self.myVars
    def close(self):
        self.myFileHandler.close()
    def __iter__(self):
        return self
    def next(self):
        values = []
        strValues = self.reader.next()
        for subString in strValues:
            try:
                value = int(subString)
            except:
                try:
                    value = float(subString)
                except:
                    value = subString
            values.append(value)
        return values

class oCSV:
    def __init__(self, fileName, variableNames):
        self.myFileHandler = open(fileName, "w")
        self.myVars = variableNames
        self.writer = csv.writer(self.myFileHandler, lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
        self.writer.writerow(self.myVars)
    def save(self, record):
        self.writer.writerow(record)
    def close(self):
        if self.myFileHandler != sys.stdout:
            self.myFileHandler.close()

