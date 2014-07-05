import cPickle as pickle

from m.common import GeneratorBase, MiningError

class iPickle(GeneratorBase):
    def __init__(self, fileHandler):
        GeneratorBase.__init__(self)
        self.myFileHandler = fileHandler
        self.myVars = pickle.load(self.myFileHandler)
    def __iter__(self):
        return self
    def close(self):
        self.myFileHandler.close()
    def next(self):
        try:
            values = pickle.load(self.myFileHandler)
            return values
        except ImportError as e:
            raise MiningError(str(e))
        except:
            raise StopIteration

    def getVariableNames(self):
        return self.myVars

class oPickle:
    def __init__(self, fileName, variableNames):
        self.myFileName = fileName
        self.myFileHandler = open(fileName, "wb")
        self.myVars = variableNames
        pickle.dump(self.myVars, self.myFileHandler, -1)
    def save(self, record):
        pickle.dump(record, self.myFileHandler, -1)
    def close(self):
        self.myFileHandler.close()


