import logging
import os

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
toolsLog = NullLogger()
toolsLogEnabled = False

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
    global toolsLog
    global toolsLogEnabled


    logging.basicConfig(
        level = logging.DEBUG,
        filename = getMainLogFileName(),
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
            compileLog = logger
            compileLogEnabled = True
        elif mode == "install":
            installLog = logger
            installLogEnabled = True
        elif mode == "complete":
            completeLog = logger
            completeLogEnabled = True
        elif mode == "tools":
            toolsLog = createLog("miner-tools")
            toolsLogEnabled = True

# Special logger
def createLog(logName):
    log = logging.getLogger(logName)
    logFh = logging.FileHandler(logName + '.log')
    logFh.setLevel(logging.INFO)
    logFormatter = logging.Formatter('%(asctime)-15s %(levelname)s:%(filename)10s:%(lineno)4d:%(funcName)s: %(message)s')
    logFh.setFormatter(logFormatter)
    log.addHandler(logFh)
    return log

def isEnabled(log):
    return not isinstance(log, NullLogger)

def isModeEnabled(mode):
    return mode in _debugModes

_mainLogFileName = None
def getMainLogFileName():
    global _mainLogFileName
    if not _mainLogFileName:
        _mainLogFileName = os.path.abspath("miner.log")
    return _mainLogFileName
