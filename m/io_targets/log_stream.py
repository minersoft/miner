from m.common import GeneratorBase
import sys
import re

class iRaw(GeneratorBase):
    def __init__(self, fileHandler):
        GeneratorBase.__init__(self)
        self.myFileHandler = fileHandler
    def __iter__(self):
        return self
    def close(self):
        self.myFileHandler.close()
    def next(self):
        try:
            while True:
                line = self.myFileHandler.readline()
                if not line :
                    raise StopIteration
                break
            values = self.getValues(line)
            return values
        except EOFError:
            raise StopIteration

    def getVariableNames(self):
        return ["line"]
    def getValues(self, line):
        return [line.rstrip('\n')]

class iLog(iRaw):
    def __init__(self, fileHandler, FS="\s+"):
        iRaw.__init__(self, fileHandler)
        self.myRexpFS = re.compile(FS)
    def getVariableNames(self):
        return ["line", "words", "NR"]
    def getValues(self, line):
        line = line.strip('\n')
        words = self.myRexpFS.split(line)
        return [line, words, len(words)]

class iTsv(iLog):
    def __init__(self, fileHandler):
        iLog.__init__(self, fileHandler, FS="\t")

class oRaw:
    def __init__(self, fileName, variableNames):
        self.myFileName = fileName
        if fileName == "stdout":
            self.myFileHandler = sys.stdout
        else:
            self.myFileHandler = open(fileName, "w")
        self.myVars = variableNames
    def save(self, record):
        self.myFileHandler.write(self.recordToString(record))
    def recordToString(self, record):
        return "".join(str(e) for e in record) + "\n"
    def close(self):
        if self.myFileHandler != sys.stdout:
            self.myFileHandler.close()


class oLog(oRaw):
    def __init__(self, fileName, variableNames, FS=" ", showVariables=False):
        oRaw.__init__(self, fileName, variableNames)
        if showVariables:
            self.myFileHandler.write(FS.join(variableNames) + "\n")
        self.myOFS = FS
    def recordToString(self, record):
        return self.myOFS.join(str(e) for e in record) + "\n"

class oTsv(oLog):
    def __init__(self, fileHandler, variableNames):
        oLog.__init__(self, fileHandler, FS="\t")
