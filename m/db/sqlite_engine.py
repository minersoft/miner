# 
# Copyright Michael Groys, 2014
#
import std_engine
import m.common as common

class SQLiteEngine(std_engine.Engine):
    def __init__(self):
        std_engine.Engine.__init__(self)
    def connect(self, dbtype, parsedUrl, **kwargs):
        if not isinstance(parsedUrl, basestring):
            raise common.MiningError("sqlite uri should be local file path or file.sqlite:///... ")
        import sqlite3
        try:
            return std_engine.Connection(sqlite3.connect(parsedUrl), self, kwargs)
        except Exception as e:
            raise common.MiningError("Failed to connect to database: %s" % str(e))
        
    def getTableNamesQuery(self):
        return """SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"""
