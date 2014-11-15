#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *
from select import SelectCommand

def p_expand_command(p):
    '''command : EXPAND expression AS id_list'''
    p[0] = ExpandCommand(p[2], p[4])

def p_expand_command_select(p):
    '''command : EXPAND expression AS id_list SELECT named_expression_list'''
    p[0] = ExpandCommand(p[2], p[4], p[6])

class ExpandCommand(SelectCommand):
    NAME = "EXPAND"
    SHORT_HELP = "EXPAND exp as name [, ...] [SELECT <repeated-exp>, ...] - expands iterable expression"
    LONG_HELP = """EXPAND exp as name [, ...] [SELECT <repeated-exp>, ...]
    Expands iterable expressions (e.g. lists, dictionaries, sets) to multiple records
    
    For example:
        EXPAND request.path.split("/") as component SELECT len(component), request.param["id"]
        EXPAND request.params.iteritems() as paramName, paramValue
"""
    MORE_SYMBOLS_FOR_COMPLETION = ['SELECT']
    def __init__(self, iterableExpr, nameList, namedExpressions=None):
        SelectCommand.__init__(self)
        self.myIterableExpr = iterableExpr
        self.myNameList = nameList
        if namedExpressions:
            for exp in namedExpressions:
                self.add(exp)
    def getVariableNames(self):
        return self.myNameList + SelectCommand.getVariableNames(self)
    def getReturnValues(self):
        return self.myNameList + SelectCommand.getReturnValues(self)
    def getBody(self):
        if len(self.myNameList) == 1:
            s = """
        for %s in %s:
            yield %s
""" % (self.myNameList[0], self.myIterableExpr.getValue(), self.getReturn())
        else:
            s = """
        for %s in %s:
            yield %s
""" % (createTupleString(self.myNameList), self.myIterableExpr.getValue(), self.getReturn())
        return s

miner_globals.addHelpClass(ExpandCommand)
miner_globals.addKeyWord(command="EXPAND")

