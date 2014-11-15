# 
# Copyright Michael Groys, 2014
#

_statements = set()

_flowCommands = set()

_srcCommands = set()
_dstCommands = set()
_keywords = set()

_switchToFileMode = set()

_startCommand = set()
_nextCommand = set()

def addKeyWord(keyword=None, statement=None, command=None, srcCommand=None, dstCommand=None, switchesToFileMode=False):
    name = None
    if keyword:
        name = keyword
        _keywords.add(name)
    elif statement:
        name = statement
        _statements.add(name)
        _startCommand.add(name)
    elif command:
        name = command
        _flowCommands.add(name)
        _nextCommand.add(name)
    elif srcCommand:
        name = srcCommand
        _srcCommands.add(name)
        _startCommand.add(name)
    elif dstCommand:
        name = dstCommand
        _dstCommands.add(name)
        _nextCommand.add(name)
    if switchesToFileMode:
        _switchToFileMode.add(name)

def shouldSwitchToFileMode(id):
    return id in _switchToFileMode

def getStartCommands():
    return _startCommand

def getNextCommands():
    return _nextCommand

def getAllKeyWords():
    return _startCommand | _nextCommand | _keywords
