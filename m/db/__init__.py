import engine_interface
import m.common as common
from m.common import MiningError

_engineMap = {}

def registerEngine(name, engine):
    _engineMap[name] = engine

def parseUri(uri):
    import urlparse
    import sys
    dbtypeSepLoc = uri.find("://")
    if dbtypeSepLoc == -1:
        return ("file", uri)
    dbtype = uri[:dbtypeSepLoc]
    value = uri[dbtypeSepLoc+3:]
    if value[0] == "/":
        if sys.platform == "win32":
            return (dbtype, dbtype[1:].replace("/", "\\"))
        else:
            return (dbtype, value[1:].replace("/", "\\"))
    parsedUrl = urlparse.urlparse(uri)
    return (dbtype, parsedUrl)

def connect(uri, **kwargs):
    dbtype, parsedUrl = parseUri(uri)
    engine = _engineMap.get(dbtype)
    if not engine:
        raise MiningError("DB engine %s is not known" % dbtype)
    return engine.connect(dbtype, parsedUrl, **kwargs)
