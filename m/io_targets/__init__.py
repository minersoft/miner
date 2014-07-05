from csv_target import *
from pickle_stream import *
from stdout import *
from log_stream import *
from json_file import *
from miner_globals import extensionToTypeMap, typeToClassMap, getClassFromImported
from m.common import *

def getTypeByExtension(extension):
    try:
        return extensionToTypeMap.get(extension, None)
    except:
        raise UnknownExtensionType(extension)
    

def getInputStreamClassName(inputType):
    className = typeToClassMap.get(inputType, None)
    if not className:
        raise UnknownTarget(inputType)
    elif not className[0]:
        raise NoInputStream(inputType)
    else:
        return className[0]

def getOutputStreamClassName(outputType):
    className = typeToClassMap.get(outputType, None)
    if not className:
        raise UnknownTarget(outputType)
    elif not className[1]:
        raise NoOutputStream(outputType)
    else:
        return className[1]

def findClass(dictionary, nameList):
    val = dictionary.get(nameList[0], None)
    if not val:
        return None  
    if len(nameList) > 1:
        if not isinstance(val, dict):
            return None
        else:
            return findClass(val, nameList[1:])
    return val

def getInputStreamClass(inputType):
    import miner_globals
    iStreamName = getInputStreamClassName(inputType)
    nameList = iStreamName.rsplit('.', 2)
    if len(nameList) == 1 or (nameList[0] == "io_targets"):
        iStreamClass = findClass(globals(), [nameList[-1]])
    else:
        iStreamClass = getClassFromImported(nameList[0], nameList[1])
    if not iStreamClass:
        raise FailedToCreateIStreamByName(iStreamName)
    return iStreamClass

def iStreamFactory(inputType, fileName, streamVars):
    iStreamClass = getInputStreamClass(inputType)
    return iStreamClass(fileName, **streamVars)

__all__ = ['getTypeByExtension', 'getInputStreamClass', 'getInputStreamClassName', 'getOutputStreamClassName', 'iStreamFactory', 'UnexistingIStream']


