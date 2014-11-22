import engine_interface
import m.common as common
from m.common import MiningError

_engineMap = {}

def registerEngine(name, engine):
    """registerEngine(name, engine) - Register new database engine
    <name> is the url scheme name e.g. 'mysql' or 'file.db'
    <engine> should implement engine_interface API
    """
    _engineMap[name] = engine

def duplicateEngine(name1, name2):
    '''duplicateEngine(name1, name2) - duplicates existing engine with different name'''
    engine = _engineMap.get(name1)
    if not engine:
        raise MiningError("DB engine %s is not known" % name1)
    _engineMap[name2] = engine

def parseUri(uri):
    import urlparse
    import sys
    from os.path import splitext
    dbtypeSepLoc = uri.find("://")
    if dbtypeSepLoc == -1:
        root, ext = splitext(uri)
        return ("file"+ext, uri)
    if len(uri) < 4:
        raise MiningError("Invalid URI format '%s' " % uri)
    dbtype = uri[:dbtypeSepLoc]
    value = uri[dbtypeSepLoc+3:]
    if dbtype=='file' and len(value)>1 and value[0] == "/":
        if sys.platform == "win32":
            value = value[1:].replace("/", "\\")
        root, ext = splitext(value)
        dbtype = "file"+ext        
        return (dbtype, value)
    parsedUrl = urlparse.urlparse(uri)
    return (dbtype, parsedUrl)

def connect(uri, **kwargs):
    """ connect(uri, **kwargs) - connects to database
    <uri> - database uri, e.g.: file.db, mysql://username:password@hostname:111/database
    <**kwargs> database specific named arguments
    """
    dbtype, parsedUrl = parseUri(uri)
    engine = _engineMap.get(dbtype)
    if not engine:
        raise MiningError("DB engine %s is not known" % dbtype)
    return engine.connect(dbtype, parsedUrl, **kwargs)
