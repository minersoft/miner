# 
# Copyright Michael Groys, 2014
#

# This module defines api for interaction between miner and databases

class FetchCursorInterface(object):
    """Abstract interface for fetching query result data"""
    def __init__(self):
        pass
    def getColumnNames(self):
        raise NotImplementedError
    def getNumColumns(self):
        raise NotImplementedError
    def __iter__(self):
        raise NotImplementedError
    def close(self):
        pass

class ConnectionInterface(object):
    """Abstract interface for database connection"""
    def close(self):
        raise NotImplementedError
    def commit(self):
        pass
    def getTableNames(self):
        return []
    def fetch(self, query, *params, **env):
        """
        Fetches data from database,
          params - define query parameters 
          env - set of optional parameters that control query execution
          returns FetchCursorInterface for iteration over results
        """
        raise NotImplementedError
    def push(self, statement, seq_of_params, **namedParams):
        """
        Fetches data from database,
          params - define query parameters 
          env - set of optional parameters that control query execution
        """ 
        raise NotImplementedError
    def execute(self, statement, *params, **env):
        """
        General statement execution
          params - define query parameters 
          env - set of optional parameters that control query execution 
        """
        raise NotImplementedError

class EngineInterface(object):
    """Database engine"""
    def __init__(self):
        pass
    def connect(self, dbtype, parsedUrl, **kwargs):
        raise NotImplementedError
