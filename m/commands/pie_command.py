#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *

def p_pie_command(p):
    '''command : PIE named_expression
               | PIE named_expression '%' '''
    inPercents = (len(p) == 4)
    p[0] = PieCommand(p[2], inPercents)

class PieCommand(TypicalCommand):
    NAME = "PIE"
    SHORT_HELP = "PIE <expression> [as <name>] [%] - generates relative distribution"
    LONG_HELP = """PIE <expression> [as <name>]
PIE <expression> [as <name>] %
    Generates relative values for distribution
"""
    def __init__(self, expression, inPercents):
        TypicalCommand.__init__(self)
        self.myExpression = expression
        self.inPercents = inPercents
    def createGenerator(self, name, parentGeneratorName):
        e_refs = ", ".join("e[1][%d]"%i for i in range(len(self.myParent.getVariableNames())))
        s = """
def %s():
    _sum = 0
    _stored = []
    for _record in %s():
        %s = _record
        _val = %s
        _sum += _val
        _stored.append( (_val, _record) )
    return [ (%s, float(e[0])/_sum %s) for e in sorted(_stored, reverse=True)]

""" % (name, parentGeneratorName, createTupleString(self.myParent.getVariableNames()), self.myExpression.getValue(), e_refs, "*100" if self.inPercents else "")
        return s

    def getVariableNames(self):
        name = self.myExpression.getName()
        if not name:
            name = "_" + str(len(self.myParent.getVariableNames())+1)
        return self.myParent.getVariableNames() + [name]

miner_globals.addHelpClass(PieCommand)
miner_globals.addKeyWord(command="PIE")

