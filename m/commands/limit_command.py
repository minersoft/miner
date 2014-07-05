#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

import miner_globals
from base import *

def p_limit_command(p):
    '''command : LIMIT integer'''
    p[0] = LimitCommand(int(p[2]))

def p_limit_if_command(p):
    '''command : LIMIT IF expression'''
    p[0] = LimitIfCommand(p[3])

def p_limit_by_command(p):
    '''command : LIMIT expression BY expression'''
    p[0] = LimitByCommand(p[2], p[4])

#
# Implementation
#
class LimitCommand(TypicalCommand):
    NAME = "LIMIT N"
    SHORT_HELP = "LIMIT <number> - limits number of records passed through this chain"
    LONG_HELP = """LIMIT <number>
    Only specified number of records will pass further.
    Reading of additional records will be stopped, but in most cases more then specified number of records will be
    processed in the chains before the limit chain
"""
    MORE_SYMBOLS_FOR_COMPLETION = ['IF', 'BY']
    def __init__(self, limit):
        TypicalCommand.__init__(self)
        self.myLimit = limit
    def getStart(self):
        return """
    _limit = %s
    if _limit == 0:
        return
    _current = 0
""" % self.myLimit
    def getBody(self):
        return """
        yield %s
        _current += 1
        if _current == _limit:
            break
""" % createTupleString(self.getVariableNames())

    def getVariableNames(self):
        return self.myParent.getVariableNames()

class LimitIfCommand(TypicalCommand):
    NAME = "LIMIT IF"
    SHORT_HELP = "LIMIT IF <expression> - limits processing of input until expression is True"
    LONG_HELP = """LIMIT IF <expression>
    Limits processing of input until expression is True.
    Reading of additional records will be stopped, but in most cases more then specified number of records will be
    processed in the chains before the limit chain
"""
    def __init__(self, expression):
        TypicalCommand.__init__(self)
        self.myExpression = expression
    def getBody(self):
        return """
        if not %s:
            break
        else:
            yield %s
""" % (self.myExpression.getValue(), createTupleString(self.getVariableNames()))

    def getVariableNames(self):
        return self.myParent.getVariableNames()

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        return globalExps + self.myExpression.getGlobalExpressions()


class LimitByCommand(TypicalCommand):
    NAME = "LIMIT BY"
    SHORT_HELP = "LIMIT <delta> BY <expression> - limits processing of input until expression changes by delta"
    LONG_HELP = """LIMIT <delta> BY <expression>
    Limits processing of input until expression expression is:
        * Becomes >= start + delta, if delta > 0
        * Becomes <= start + delta, if delta < 0
        * Becomes != start,         if delta == 0
    Reading of additional records will be stopped, but in most cases more then specified number of records will be
    processed in the chains before the limit chain
"""
    def __init__(self, delta, expression):
        TypicalCommand.__init__(self)
        self.myDelta = delta
        self.myExpression = expression
    def getStart(self):
        return """
    _delta = %s
    if _delta < 0:
        _multiplicator = -1
    else:
        _multiplicator = 1
    _startIsDefined = False
""" % self.myDelta.getValue()

    def getBody(self):
        return """
        _value = %s
        if not _startIsDefined:
            _startIsDefined = True
            _start = _value
        if _delta == 0:
            if _value != _start:
                break
        elif _multiplicator * (_value - (_start + _delta)) >= 0:
            break
        yield %s
""" % (self.myExpression.getValue(), createTupleString(self.getVariableNames()))

    def getVariableNames(self):
        return self.myParent.getVariableNames()

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        return globalExps + self.myExpression.getGlobalExpressions() +  self.myDelta.getGlobalExpressions()

miner_globals.addHelpClass(LimitCommand)
miner_globals.addCommandName("LIMIT")

miner_globals.addHelpClass(LimitIfCommand)
miner_globals.addHelpClass(LimitByCommand)

