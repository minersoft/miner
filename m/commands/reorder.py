#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

import miner_globals
from base import *
import m.common as common

def p_reorder_command(p):
    '''command : REORDER expression ',' expression BY expression'''
    p[0] = ReorderCommand(p[2], p[4], p[6])


class ReorderCommand(TypicalCommand):
    NAME = "REORDER"
    SHORT_HELP = "REORDER <range> , <bin-size> BY <expression> - applies filter to recors"
    LONG_HELP = """REORDER <range> , <bin-size> BY <expression>
    Reorders records according to the expression
    Aggregates them in the range value divided by bins
"""
    def __init__(self, valueRange, binSize, expression):
        TypicalCommand.__init__(self)
        self.valueRange = valueRange
        self.binSize = binSize
        self.myExpression = expression
    def getStart(self):
        s = TypicalCommand.getStart(self)
        s += "    _reorderer = _runtime.Reorderer(%s, %s)\n" % (self.valueRange.getValue(), self.binSize.getValue())
        return s
    def getBody(self):
        return """
        for _record in _reorderer.push(%s, %s):
            yield _record
""" % (self.myExpression.getValue(), createTupleString(self.getVariableNames()))

    def getEnd(self):
        return """
    for _record in _reorderer.flush():
        yield _record
"""
        
    def getRequiredVariables(self):
        return []

    def getVariableNames(self):
        return self.myParent.getVariableNames()

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        return globalExps + self.myExpression.getGlobalExpressions()

miner_globals.addHelpClass(ReorderCommand)
miner_globals.addCommandName("REORDER")

