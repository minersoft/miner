import m.common as common

class StatementBase(common.HelpClass):
    def __init__(self):
        pass
    def dump(self, fh):
        pass
    def dumplog(self, log, context=""):
        log.info("%sStatement %s", context, self.__class__.__name__)
