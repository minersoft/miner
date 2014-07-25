#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *
from for_command import ForSelectCommand
from m.expressions import Expression

def p_pareto_command(p):
    '''command : PARETO named_expression BY expression SELECT aggregated_named_expression_list'''
    if p[2].getName() == "":
        p[2].setName(p[4].getName())
    p[0] = ParetoCommand(p[2], p[4], p[6])

def p_pareto_of_command(p):
    '''command : PARETO named_expression OF expression SELECT aggregated_named_expression_list'''
    if p[2].getName() == "":
        p[2].setName(p[4].getName())
    p[0] = ParetoCommand(p[2], p[4], p[6], useSum=False)

def p_pareto_simple_command(p):
    '''command : PARETO named_expression SELECT aggregated_named_expression_list'''
    one = Expression()
    one.setValue(1)
    p[0] = ParetoCommand(p[2], one, p[4])

#
# Implementation
#
class ParetoCommand(ForSelectCommand):
    NAME = "PARETO"
    SHORT_HELP = "PARETO <step> [as <name>] [BY <exp>] SELECT <aggregation>, ... - generates pareto distibution"
    @staticmethod
    def LONG_HELP():
        s = """PARETO <step> [as <name>] [BY <exp>] SELECT <aggregation>, ...
    PARETO command is used to generate get aggregated values from start of stream up to current point.
        <step> - defines when to generates output
        <exp>  - What expression to evaluate while checking <step> increment
        If <exp> is not defined step specifies numberrecords to aggregate
    To get canonical pareto distribution stream before PARETO command should be sorted
Examples:
PARETO 2 BY i SELECT sum(x), min(y)
Input:
  i,x,y
  1,1,0
  1,2,1
  1,3,2
  4,4,-1
Output:
  i,x,y
  1,1,0
  3,6,0
  7,10,-1   
"""
        s += ForSelectCommand.getAggregatorsHelp()
        return s
    @staticmethod
    def MORE_SYMBOLS_FOR_COMPLETION():
        return ["BY", "SELECT"] + miner_globals.getAggregators()

    def __init__(self, step, expression, aggregatedExpressions, useSum=True):
        ForSelectCommand.__init__(self, aggregatedExpressions, 1)
        self.step = step
        self.expression = expression
        self.useSum = useSum
        if not self.step.getName():
            self.step.setName("_1")

    def getStart(self):
        s =  "    import copy\n"
        s += ForSelectCommand.getStart(self)
        s += "    _step = %s\n" % self.step.getValue()
        if self.useSum:
            s += "    _accumulated = 0\n"
        else:
            s += "    _accumulated = None\n    _next = 0\n"
        return s

    def getDictionaryValues(self):
        return "".join(("copy.copy(_d['%s'].getValue()),"%aggregated[2]) for aggregated in self.myAggregatedExpressions)

    def getBody(self):
        s = self.getAddValuesSection("_d")
        if self.useSum:
            s += """
        _delta = %s
        if _delta != 0 and ((_accumulated+_delta)//_step != _accumulated//_step):
            yield (_accumulated, %s)
        _accumulated += _delta
""" % (self.expression.getValue(), self.getDictionaryValues())
        else:
            s += """
        if _accumulated is None:
            _accumulated = %s
            _next = _accumulated + _step
        else:
            _accumulated = %s
        if _accumulated >= _next:
            yield (_accumulated, %s)
            _next += _step
            while _next <= _accumulated:
                _next += _step
""" % (self.expression.getValue(), self.expression.getValue(), self.getDictionaryValues())
        return s
    def getEnd(self):
        return ""
    def getVariableNames(self):
        return [self.step.getName()] + ForSelectCommand.getVariableNames(self)

miner_globals.addHelpClass(ParetoCommand)
miner_globals.addCommandName("PARETO")


                


