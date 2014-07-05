import json
from m.common import GeneratorBase

class iJson(GeneratorBase):
    def __init__(self, fileHandler):
        GeneratorBase.__init__(self)
        self.myFileHandler = fileHandler
    def __iter__(self):
        return self
    def close(self):
        self.myFileHandler.close()
    def next(self):
        try:
            obj = json.load(self.myFileHandler)
            return (obj, )
        except:
            raise StopIteration

    def getVariableNames(self):
        return ("obj", )
