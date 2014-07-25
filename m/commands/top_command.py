#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *

def p_top_command(p):
    '''command : TOP integer expression'''
    p[0] = TopCommand(p[2], p[3])

def p_bottom_command(p):
    '''command : BOTTOM integer expression'''
    p[0] = BottomCommand(p[2], p[3])

class TopCommand(CommandBase):
    NAME = "TOP"
    SHORT_HELP = "TOP <number> expression - Returns at most <number> of top records ordered by expression"
    LONG_HELP = """TOP <number> expression
    Returns <number> of records with maximum values of expression in decreasing order
    Heap sorting is used. O(n*log(number))
"""
    def __init__(self, number, exp, ascending=False):
        CommandBase.__init__(self)
        self.myNumber = number
        self.myExpression = exp
        self.myAscending = ascending
    def getVariableNames(self):
        return self.myParent.getVariableNames()
    def createGenerator(self, name, parentGeneratorName):
        op = "heapq.nsmallest" if self.myAscending else "heapq.nlargest"
        s = """
def %s():
    import heapq
    def getkey( record ):
        %s = record
        return %s
    allData = %s(%s, %s(), key=getkey)
    return allData

""" % (name, createTupleString(self.getVariableNames()), self.myExpression.getValue(), op, self.myNumber, parentGeneratorName)
        return s

class BottomCommand(TopCommand):
    NAME = "BOTTOM"
    SHORT_HELP = "BOTTOM <number> expression - Returns at most <number> of bottom records ordered by expression"
    LONG_HELP = """BOTTOM <number> expression
    Returns <number> of records with minimum values of expression in increasing order
    Heap sorting is used. O(n*log(number))
"""
    def __init__(self, number, exp):
        TopCommand.__init__(self, number, exp, ascending = True)

miner_globals.addCommandName("TOP")
miner_globals.addCommandName("BOTTOM")
miner_globals.addHelpClass(TopCommand)
miner_globals.addHelpClass(BottomCommand)

