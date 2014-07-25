#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *

def p_if_command(p):
    '''command : IF expression'''
    p[0] = IfCommand(p[2])

def p_if_command_prepare_list(p):
    '''command : IF '[' named_parameter_list ']' expression'''
    p[0] = IfCommand(p[3], p[5])


class IfCommand(TypicalCommand):
    NAME = "IF"
    SHORT_HELP = "IF expression - applies filter to recors"
    LONG_HELP = """IF expression
    Passes only records which eveluate expression to True.
    Record itself is not changed
"""
    def __init__(self, expression, preparationList=None):
        TypicalCommand.__init__(self, preparationList)
        self.myExpression = expression
    def getBody(self):
        return """
        if %s:
            yield %s
""" % (self.myExpression.getValue(), createTupleString(self.getVariableNames()))

    def getRequiredVariables(self):
        return []

    def getVariableNames(self):
        return self.myParent.getVariableNames()

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        return globalExps + self.myExpression.getGlobalExpressions()


miner_globals.addHelpClass(IfCommand)
miner_globals.addCommandName("IF")

