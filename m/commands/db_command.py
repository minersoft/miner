# 
# Copyright Michael Groys, 2014
#

import miner_globals
import m.common as common
import m.db_connections
import re
from base import *
from m.utilities import decodeStr

def p_db_fetch_command(p):
    '''source : DB ID FETCH expression'''
    p[0] = DbFetch(p[2], p[4])

class DbFetch(CommandBase):
    NAME = "DB FETCH"
    SHORT_HELP = "DB <db-connection> FETCH 'query' - Gets mining data from result of database query"
    LONG_HELP = """DB <db-connection> FETCH 'query'
    Gets mining data from result of database query, e.g.
       DB conn FETCH 'SELECT * FROM table' """
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return m.db_connections.completionState(input, pos)
    def __init__(self, dbId, queryExp):
        self.dbId = dbId
        self.queryExp = queryExp
        self.myVars = None
        self.cursor = None

    def initCursor(self):
        if self.cursor:
            return
        m.db_connections.checkConnection(self.dbId)
        
        try:
            self.cursor = miner_globals.evalExpression("%s.fetch(%s)" % (self.dbId, self.queryExp.getValue()))
        except Exception as e:
            raise common.CompilationError(str(e))
    
    VALID_ID_REGEXP = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*$')
    def getVariableNames(self):
        self.initCursor()
        if self.myVars:
            return self.myVars
        columnNames = self.cursor.getColumnNames()
        autoId = 1
        self.myVars = []
        for name in columnNames:
            if DbFetch.VALID_ID_REGEXP.match(name):
                self.myVars.append(name)
            else:
                self.myVars.append("_"+str(autoId))
                autoId += 1
        return self.myVars

    def getExportedGlobals(self, name):
        self.initCursor()
        return {name + "_cursor": self.cursor}
    

    def createLoader(self, loaderName):
        s = """
def %s():
    global readRecords
    if _runtime.isVerbose():
        print '''-- Mining %s ...'''
    for r in %s_cursor:
        readRecords += 1
        yield r
""" %   (loaderName, self.dbId, loaderName)
        return s
    
    def getFinalizeAction(self):
        self.initCursor()
        return self.cursor.close


miner_globals.addHelpClass(DbFetch)
miner_globals.addKeyWord(srcCommand="DB")
miner_globals.addKeyWord(keyword="FETCH")

