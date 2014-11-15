#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
import m.common as common
from base import *

def p_accumulate_coals(p):
    '''command :
               | ACCUMULATE'''
    p[0] = DefaultAccumulateCommand()

def p_accumulate_command(p):
    '''command : ACCUMULATE id_list BY expression'''
    p[0] = AccumulateCommand(p[2], p[4])


class AccumulateCommand(TypicalCommand):
    NAME = "ACCUMULATE BY"
    SHORT_HELP = "ACCUMULATE id [,...] BY accumulatorClass - accumulates coal records"
    LONG_HELP = """ACCUMULATE id [,...] BY accumulatorClass
    Performs custom accumulation logic.
"""
    def __init__(self, accumulatorVariables, accumulatorClass):
        TypicalCommand.__init__(self)
        self.myAccumulatorVariables = accumulatorVariables
        self.myAccumulatorClass = accumulatorClass
        self.yieldVal = "(accumulated,)" if len(self.myAccumulatorVariables)==1 else "accumulated"
    def getStart(self):
        return """
    import types
    _acc = %s
    if isinstance(_acc,types.ClassType):
        accumulator = _acc()
    else:
        accumulator = _acc
    """ % self.myAccumulatorClass
        
    def getBody(self):
        return """
        for accumulated in accumulator.accumulate(%s):
            yield %s
""" % (", ".join(self.myAccumulatorVariables), self.yieldVal)

    def getEnd(self):
        return """
    for accumulated in accumulator.finish():
        yield %s
""" % self.yieldVal
    def getRequiredVariables(self):
        return []

    def getVariableNames(self):
        return self.myAccumulatorVariables

class DefaultAccumulateCommand(TypicalCommand):
    NAME = "ACCUMULATE"
    SHORT_HELP = "ACCUMULATE|<empty> - accumulates coal records"
    LONG_HELP = """ACCUMULATE
<empty>
    Performs context dependent accumulation, e.g.
      Accumulates coal records according to the sysId, vaId, flowId and transactionId
      coal record is released when decoding information becomes available
      or accumulates frecords belonging to the same transaction
ACCUMULATE id [,...] BY accumulatorClass[(params)]
    Performs custom accumulation
"""
    def setParent(self, parent):
        GeneratorBase.setParent(self, parent)
        self.accumulatorTuple = miner_globals.getAccumulator(self.myParent.getVariableNames())
    def getStart(self):
        if not self.accumulatorTuple:
            raise common.CompilationError("Invalid input for accumulation")
        return """    accumulator = %s()\n""" % self.accumulatorTuple[1]
    def getBody(self):
        return """
        for accumulated in accumulator.accumulate(%s):
            yield (accumulated, )
""" % self.accumulatorTuple[0]
    def getEnd(self):
        return """
    for accumulated in accumulator.finish():
        yield (accumulated, )
"""

    def getRequiredVariables(self):
        return [self.accumulatorTuple[0]]

    def getVariableNames(self):
        return [self.accumulatorTuple[0]]

miner_globals.addHelpClass(AccumulateCommand)
miner_globals.addHelpClass(DefaultAccumulateCommand)
miner_globals.addKeyWord(command="ACCUMULATE")
miner_globals.addKeyWord(keyword="BY")
