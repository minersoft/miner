# 
# Copyright Michael Groys, 2014
#
import std_engine
import m.common as common

class SQLiteConnection(std_engine.Connection):
    def __init__(self, dbconnection, engine):
        std_engine.Connection.__init__(self, dbconnection, engine)
    # SQLite require params as tuple thus we need to map None to tuple
    def fetch(self, query, params=None):
        if params is None:
            params = ()
        return std_engine.Connection.fetch(self, query, params)
    def execute(self, query, params=None):
        if params is None:
            params = ()
        std_engine.Connection.execute(self, query, params)
    def executemany(self, query, seq_of_params):
        if seq_of_params is None:
            seq_of_params = ()
        std_engine.Connection.executemany(self, query, seq_of_params)


class SQLiteEngine(std_engine.Engine):
    def __init__(self):
        std_engine.Engine.__init__(self)
    def connect(self, dbtype, parsedUrl, **kwargs):
        if not isinstance(parsedUrl, basestring):
            raise common.MiningError("sqlite url should be local file path or file:///... URL")
        import sqlite3
        try:
            return SQLiteConnection(sqlite3.connect(parsedUrl), self)
        except Exception as e:
            raise common.MiningError("Failed to connect to database: %s" % str(e))
        
    def getTableNamesQuery(self):
        return """SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"""
