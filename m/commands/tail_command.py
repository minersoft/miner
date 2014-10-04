#
# Copyright Michael Groys, 2014
#

import miner_globals
from base import *
from m.common import COMPLETE_NONE

def p_command_sortby_command(p):
    '''command : TAIL integer'''
    p[0] = TailCommand(p[2])

class TailCommand(CommandBase):
    NAME = "TAIL"
    SHORT_HELP = "TAIL <number> - return <number> of last records"
    LONG_HELP = """TAIL <number>
    Returns <number> of last records without modifying their order
"""
    COMPLETION_STATE = COMPLETE_NONE
    
    def __init__(self, N):
        CommandBase.__init__(self)
        self.N = N
    def getVariableNames(self):
        return self.myParent.getVariableNames()
    def createGenerator(self, name, parentGeneratorName):
        s = """
def %s():
    N = %s
    l = [None] * N
    i = 0
    for r in %s():
        l[i%%N] = r
        i += 1
    start = max(0, i-N)
    for j in range(start, i):
        yield l[j%%N]

""" % (name, self.N, parentGeneratorName)
        return s
    def getGlobalExpressions(self):
        return []
    
    
miner_globals.addHelpClass(TailCommand)
miner_globals.addCommandName("TAIL")

