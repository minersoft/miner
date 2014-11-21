# 
# Copyright Michael Groys, 2014
#

from miner_globals import setVariable, removeVariable, getVariable
from m.common import CompilationError

_db_connections = set()


def addDbConnecton(name, value):
    _db_connections.add(name)
    setVariable(name, value)

def closeDbConnection(name):
    if name not in _db_connections:
        raise CompilationError( "Db connection '%s' doesn't exist" % name)

    removeVariable(name)
    _db_connections.remove(name)

def getConnection(name):
    if name not in _db_connections:
        raise CompilationError( "Db connection '%s' doesn't exist" % name)
    return getVariable(name)

def checkConnection(name):
    if name not in _db_connections:
        raise CompilationError( "Db connection '%s' doesn't exist" % name)

def getConnectionNames():
    return list(_db_connections)

def completionState(input, pos):
    import m.common as common
    if pos==0:
        return common.COMPLETE_NONE
    tokens = input[:pos].split()
    l = len(tokens)
    if input[pos-1].isspace():
        l += 1
    if l<=1:
        return common.COMPLETE_NONE
    elif l==2:
        return list(_db_connections) + ["CONNECT"]
    else:
        if tokens[1] == "CONNECT":
            if l==3:
                return common.COMPLETE_FILE
            else:
                return common.COMPLETE_NONE
        else:
            if l==3:
                return ['CLOSE', 'TABLES', 'EXECUTE', 'FETCH']
            else:
                return common.COMPLETE_SYMBOLS

