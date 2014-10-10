import logging

class NullLogger:
    def debug(self,msg,*args,**kwargs):
        pass
    def info(self,msg,*args,**kwargs):
        pass
    def warning(self,msg,*args,**kwargs):
        pass
    def error(self,msg,*args,**kwargs):
        pass

_debugModes = set()
mainLog = NullLogger()
mainLogEnabled = False
lexLog = NullLogger()
lexLogEnabled = False
parseLog = NullLogger()
parseLogEnabled = False
compileLog = NullLogger()
compileLogEnabled = False
installLog = NullLogger()
installLogEnabled = False
completeLog = NullLogger()
completeLogEnabled = False

def setDebugModes(debugModes):
    global _debugModes
    global mainLog
    global mainLogEnabled
    global lexLog
    global lexLogEnabled
    global parseLog
    global parseLogEnabled
    global compileLog
    global compileLogEnabled
    global installLog
    global installLogEnabled
    global completeLog
    global completeLogEnabled


    logging.basicConfig(
        level = logging.DEBUG,
        filename = "miner.log",
        filemode = "w",
        format = "%(asctime)-15s %(filename)10s:%(lineno)4d:%(funcName)s: %(message)s"
    )
    logger = logging.getLogger()
    for mode in debugModes:
        _debugModes.add(mode)
        if mode == "main":
            mainLog = logger
            mainLogEnabled = True
        elif mode == "lex":
            lexLog = logger
            lexLogEnabled = True
        elif mode == "parse":
            parseLog = logger
            parseLogEnabled = True
        elif mode == "compile":
            print "CCCC"
            compileLog = logger
            compileLogEnabled = True
        elif mode == "install":
            installLog = logger
            installLogEnabled = True
        elif mode == "complete":
            completeLog = logger
            completeLogEnabled = True

# Special logger
def createLog(logName):
    log = logging.getLogger(logName)
    logFh = logging.FileHandler(logName + '.log')
    logFh.setLevel(logging.INFO)
    logFormatter = logging.Formatter('%(asctime)s: %(message)s')
    logFh.setFormatter(logFormatter)
    log.addHandler(logFh)
    return log

def isEnabled(log):
    return not isinstance(log, NullLogger)
