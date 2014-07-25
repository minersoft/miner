#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *

def p_command_sortby_command(p):
    '''command : sortby_command'''
    p[0] = p[1]

def p_sortby_command(p):
    '''sortby_command : SORTBY not_empty_expression_list'''
    p[0] = SortbyCommand(p[2], True)

def p_sortby_direction_command(p):
    '''sortby_command : SORTBY not_empty_expression_list ascending'''
    p[0] = SortbyCommand(p[2], p[3])

class SortbyCommand(CommandBase):
    NAME = "SORTBY"
    SHORT_HELP = "SORTBY expression [,...] [ASC|DESC] - sorts records by expression"
    LONG_HELP = """SORTBY expression [,...] [ASC|DESC]
    Sorts recors according to the expression. Default order is ascending. 
    As usual algorith is O(N) in space and O(N*logN) in time
    Although it is stable meaning that the order of records with the same key remains unchanged
"""
    MORE_SYMBOLS_FOR_COMPLETION = ['ASC', 'DESC']
    def __init__(self, expList, ascending):
        CommandBase.__init__(self)
        self.myExpressionList = expList
        self.myAscending = ascending
    def getVariableNames(self):
        return self.myParent.getVariableNames()
    def createGenerator(self, name, parentGeneratorName):
        s = """
def %s():
    def getkey( record ):
        %s = record
        return %s
    allData = sorted(%s(), key=getkey %s)
    return allData

""" % (name, createTupleString(self.getVariableNames()), self.getSortKey(), parentGeneratorName, "" if self.myAscending else ", reverse=True")
        return s
    def getSortKey(self):
        if len(self.myExpressionList):
            return self.myExpressionList[0].getValue()
        else:
            return createTupleString([e.getValue() for e in self.myExpressionList])

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        for e in self.myExpressionList:
            globalExps.extend(e.getGlobalExpressions())
        return globalExps
    
    def getReduceCommand(self, queueListStr, queueList):
        queueListStr = ", ".join( ("getnext(%s)"%q for q in queueList) )
        s = """
    import heapq
    def getnext( q ):
        while True:
            record = q.get()
            if record is None:
                break
            %s = record
            key = %s%s
            yield (key, record)
    for r in heapq.merge(%s):
        yield r[1]
""" % (createTupleString(self.getVariableNames()), "" if self.myAscending else "-", self.getSortKey(), queueListStr)
        return s
    
miner_globals.addHelpClass(SortbyCommand)
miner_globals.addCommandName("SORTBY")

