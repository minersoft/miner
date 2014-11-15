#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
import m._runtime
from base import *

def p_match_command(p):
    '''command : MATCH expression MATCH_EQ STRING'''
    p[0] = MatchCommand(p[2], p[4])

class MatchCommand(TypicalCommand):
    NAME = "MATCH"
    SHORT_HELP = "MATCH <expression> =~ <regexp>"
    LONG_HELP = """MATCH <expression> =~ <regexp>
    MATCH commands filters records that match specified regular expression (string) and extract named groups from it:
      MATCH request.path =~ r"video/(?P<start>\d+)-(?P<end>\d+)"
    After this command string variables 'start' and 'end' will be added to existing record
    You can use int(start) and int(end) to convert them to integer 
"""
    def __init__(self, expression, regExp):
        TypicalCommand.__init__(self)
        matchRegExp = m._runtime.Matcher(regExp)
        self.groupNames = matchRegExp.getGroupNames()
        self.myExpression = expression
        self.myRegExp = regExp

    def getVariableNames(self):
        return self.myParent.getVariableNames() + self.groupNames

    def getBody(self):
        return """
        if _matcher_.match(%s):
            yield %s
""" % (self.myExpression.getValue(), createTupleString(self.getReturnValues()))

    def getStart(self):
        return """
    _matcher_ = _runtime.Matcher(%s)
""" % self.myRegExp

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        return globalExps + self.myExpression.getGlobalExpressions()

    def getReturnValues(self):
        returnValues = [("_matcher_['%s']" % group) for group in self.groupNames]
        return self.myParent.getVariableNames() + returnValues


miner_globals.addHelpClass(MatchCommand)
miner_globals.addKeyWord(command="MATCH")

