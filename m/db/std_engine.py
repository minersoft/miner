# 
# Copyright Michael Groys, 2014
#

"""
This module implements connection and FetchCursor for DB API2 compatible engines 
"""

from engine_interface import *

class FetchCursor(FetchCursorInterface):
    def __init__(self, dbcursor):
        self.dbcursor = dbcursor
    def __iter__(self):
        return self
    def next(self):
        r = self.dbcursor.fetchone()
        if not r:
            raise StopIteration
        return r
    def getColumnNames(self):
        return [d[0] for d in self.dbcursor.description]
    def getNumColumns(self):
        return len(self.dbcursor.description)
    def close(self):
        del self.dbcursor

class Connection(ConnectionInterface):
    def __init__(self, dbconnection, engine):
        ConnectionInterface.__init__(self)
        self.connection = dbconnection
        self.engine = engine
    def close(self):
        self.connection.close()
    def commit(self):
        self.connection.commit()
    def fetch(self, query, params=tuple()):
        dbcursor = self.connection.cursor()
        dbcursor.execute(query, params)
        return FetchCursor(dbcursor)
    def execute(self, query, params=tuple()):
        dbcursor = self.connection.cursor()
        dbcursor.execute(query, params)
        del dbcursor
    def executemany(self, query, seq_of_params):
        dbcursor = self.connection.cursor()
        dbcursor.executemany(query, seq_of_params)
        del dbcursor
    def getTableNames(self):
        dbcursor = self.connection.cursor()
        dbcursor.execute(self.engine.getTableNamesQuery())
        tableNames = dbcursor.fetchall()
        del dbcursor
        return [t[0] for t in tableNames]
        
class Engine(EngineInterface):
    def __init__(self):
        EngineInterface.__init__(self)
    def getTableNamesQuery(self):
        raise NotImplementedError