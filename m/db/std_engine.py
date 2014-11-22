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
            self.dbcursor = None
            raise StopIteration
        return r
    def getColumnNames(self):
        return [d[0] for d in self.dbcursor.description]
    def getNumColumns(self):
        return len(self.dbcursor.description)
    def close(self):
        if self.dbcursor:
            self.dbcursor.close()
            self.dbcursor = None

class Connection(ConnectionInterface):
    def __init__(self, dbconnection, engine):
        ConnectionInterface.__init__(self)
        self.connection = dbconnection
        self.engine = engine
    def close(self):
        self.connection.close()
    def commit(self):
        self.connection.commit()
    def fetch(self, query, params=None):
        dbcursor = self.connection.cursor()
        dbcursor.execute(query, params)
        return self.createFetchCursor(dbcursor)
    def execute(self, query, params=None):
        dbcursor = self.connection.cursor()
        dbcursor.execute(query, params)
        del dbcursor
    def executemany(self, query, seq_of_params):
        dbcursor = self.connection.cursor()
        dbcursor.executemany(query, seq_of_params)
        del dbcursor
    def executemany_in_batches(self, batchSize, query, seq_of_params):
        dbcursor = self.connection.cursor()
        paramIter = iter(seq_of_params)
        try:
            while True:
                leftInBatch = batchSize
                batchParams = []
                try:
                    while leftInBatch>0:
                        batchParams.append(paramIter.next())
                        leftInBatch -= 1
                finally:
                    dbcursor.executemany(query, batchParams)
                    batchParams = []
        except StopIteration:
            pass
        
                
    def getTableNames(self):
        dbcursor = self.connection.cursor()
        dbcursor.execute(self.engine.getTableNamesQuery())
        tableNames = dbcursor.fetchall()
        del dbcursor
        return [t[0] for t in tableNames]
    def createFetchCursor(self, dbcursor, numRowsToFetchAtOnce=1):
        '''
        This function creates fetch cursor based on database cursor.
        It receives number of rows to fetch at once (this is recommendation value)
        If it is 0 - fetch all rows at once
        '''
        return FetchCursor(dbcursor)
        
class Engine(EngineInterface):
    def __init__(self):
        EngineInterface.__init__(self)
    def getTableNamesQuery(self):
        raise NotImplementedError