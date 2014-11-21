# 
# Copyright Michael Groys, 2014
#


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
    def fetch(self, query, params=None):
        """Returns Fetch cursor interface"""
        raise NotImplementedError
    def execute(self, statement, params=None):
        raise NotImplementedError
    def executemany(self, statement, seq_of_params):
        raise NotImplementedError

class EngineInterface(object):
    """Database engine"""
    def __init__(self):
        pass
    def connect(self, dbtype, parsedUrl, **kwargs):
        raise NotImplementedError
