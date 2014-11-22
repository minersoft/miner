# 
# Copyright Michael Groys, 2014
#

import miner_globals
import m.db_connections
import m.common as common
import base
import re

ID_REXP = re.compile(r"[_a-zA-Z]\w*$")
def p_db_connect_statement(p):
    '''statement : DB CONNECT FILENAME streamvar_list FILENAME FILENAME'''
    if p[5] != 'as':
        raise common.CompilerSyntaxError(p.lexpos(5), msg="'as' expected")
    if not ID_REXP.match(p[6]):
        raise common.CompilerSyntaxError(p.lexpos(6), msg="identifier expected")

    p[0] = DbConnect(p[3], p[4], p[6])
    
def p_db_close_statement(p):
    '''statement : DB ID CLOSE'''
    p[0] = DbClose(p[2])

def p_db_commit_statement(p):
    '''statement : DB ID COMMIT'''
    p[0] = DbCommit(p[2])

def p_db_tables_statement(p):
    '''statement : DB ID TABLES'''
    p[0] = DbTables(p[2])

def p_db_execute_statement(p):
    '''statement : DB ID EXECUTE expression optional_with_params'''
    p[0] = DbExecute(p[2], p[4], p[5])

class DbConnect(base.StatementBase):
    NAME = "DB CONNECT"
    SHORT_HELP = "DB CONNECT <db-connection-uri> [param1=value1]... as myDbConn - connects to database"
    LONG_HELP = """DB CONNECT <db-connection-uri> [param1=value1]... as myDbConn
    Opens new database connection"""
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return m.db_connections.completionState(input, pos)
    def __init__(self, uri, streamVars, connectionId):
        base.StatementBase.__init__(self)
        self.uri = uri
        self.streamVars = streamVars
        self.connectionId = connectionId
    def execute(self):
        import m.db
        conn = m.db.connect(self.uri, **self.streamVars)
        m.db_connections.addDbConnecton(self.connectionId, conn)

class DbClose(base.StatementBase):
    NAME = "DB CLOSE"
    SHORT_HELP = "DB myDbConn CLOSE- closes database connection"
    LONG_HELP = """DB myDbConn CLOSE
    Close open database connection"""
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return m.db_connections.completionState(input, pos)
    def __init__(self, connectionId):
        base.StatementBase.__init__(self)
        self.connectionId = connectionId
    def execute(self):
        m.db_connections.closeDbConnection(self.connectionId)

class DbCommit(base.StatementBase):
    NAME = "DB COMMIT"
    SHORT_HELP = "DB myDbConn COMMIT- commits pending transactions in db connection"
    LONG_HELP = """DB myDbConn CLOSE
    commits pending transactions in database connection"""
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return m.db_connections.completionState(input, pos)
    def __init__(self, connectionId):
        base.StatementBase.__init__(self)
        self.connectionId = connectionId
    def execute(self):
        m.db_connections.commitDbConnection(self.connectionId)

class DbTables(base.StatementBase):
    NAME = "DB TABLES"
    SHORT_HELP = "DB myDbConn TABLES- lists database tables"
    LONG_HELP = """DB myDbConn TABLES
    Close open database connection"""
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return m.db_connections.completionState(input, pos)
    def __init__(self, connectionId):
        base.StatementBase.__init__(self)
        self.connectionId = connectionId
    def execute(self):
        connection = m.db_connections.getConnection(self.connectionId)
        tableNames = connection.getTableNames()
        for name in tableNames:
            print name

class DbExecute(base.StatementBase):
    NAME = "DB EXECUTE"
    SHORT_HELP = "DB myDbConn EXECUTE 'query' - closes database connection"
    LONG_HELP = """DB myDbConn EXECUTE 'query'
    Executes generic database query"""
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return m.db_connections.completionState(input, pos)
    def __init__(self, connectionId, queryExp, paramExpList):
        base.StatementBase.__init__(self)
        self.connectionId = connectionId
        self.queryExp = queryExp
        self.paramExpList = paramExpList
    def execute(self):
        m.db_connections.checkConnection(self.connectionId)
        paramsExp = "(" + "".join((p.getValue()+", ") for p in self.paramExpList) + ")"
        try:
            miner_globals.execExpression("%s.execute(%s, %s)" % (self.connectionId, self.queryExp.getValue(), paramsExp))
        except Exception as e:
            raise common.MiningError("Execution of DB query failed: %s" % str(e))

miner_globals.addKeyWord(statement="DB")
miner_globals.addKeyWord(keyword="CONNECT", switchesToFileMode=True)
miner_globals.addKeyWord(keyword="CLOSE")
miner_globals.addKeyWord(keyword="COMMIT")
miner_globals.addKeyWord(keyword="TABLES")
miner_globals.addKeyWord(keyword="EXECUTE")

miner_globals.addHelpClass(DbConnect)
miner_globals.addHelpClass(DbClose)
miner_globals.addHelpClass(DbExecute)
