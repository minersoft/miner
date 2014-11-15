#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *
from m.expressions import Expression

def p_command_select_command(p):
    '''command : select_command'''
    p[0] = p[1]
    
def p_select_command(p):
    '''select_command : SELECT named_expression
                      | DISTINCT named_expression'''
    if p[1] == 'SELECT':
        p[0] = SelectCommand()
    elif p[1] == 'DISTINCT':
        p[0] = DistinctCommand()
    p[0].add(p[2])

def p_select_command_expression(p):
    '''select_command : select_command ',' named_expression'''
    p[0] = p[1]
    p[0].add(p[3])

def p_select_command_all(p):
    '''select_command : SELECT '*' '''
    p[0] = SelectCommand()
    p[0].add('*')

def p_select_command_all_prepare_list(p):
    '''select_command : SELECT '[' named_parameter_list ']' '*' '''
    p[0] = SelectCommand(p[3])
    p[0].add('*')

def p_select_command_add_all(p):
    '''select_command : select_command ',' '*' '''
    p[0] = p[1]
    p[0].add('*')

def p_select_command_prepare_list(p):
    '''select_command : SELECT '[' named_parameter_list ']' named_expression
                      | DISTINCT '[' named_parameter_list ']'  named_expression'''
    if p[1] == 'SELECT':
        p[0] = SelectCommand(p[3])
    elif p[1] == 'DISTINCT':
        p[0] = DistinctCommand(p[3])
    p[0].add(p[5])

######
# Implementation
######
class SelectCommand(TypicalCommand):
    NAME = "SELECT"
    SHORT_HELP = "SELECT exp1 [as name1], exp2 [as name2] ... - generates records using the specified expressions"
    LONG_HELP = """SELECT exp1 [as name1], exp2 [as name2]
SELECT '[' name = expression, ... ']' exp1 [as name1], exp2 [as name2]
    SELECT command generates record according to the expressions provided.
    The values from the chains above becomes no longe available, for example:
      SELECT coal.flowId, coal.transactionId as TID
        will generate records with two variable flowId and TID and you will not be able to refer to coal itself anymore
"""
    def __init__(self, preparationList=None):
        TypicalCommand.__init__(self, preparationList)
        self.expressions = []
    def add(self, exp):
        if exp == '*':
            pass
        elif not exp.getName():
            name = "_%d" % (len(self.expressions)+1)
            exp.setName(name)
        self.expressions.append( exp )
    def setParent(self, parent):
        GeneratorBase.setParent(self, parent)
        try:
            pos = self.expressions.index('*')
            del self.expressions[pos]
            for var in self.myParent.getVariableNames():
                exp = Expression()
                exp.setId(var)
                self.expressions.insert(pos, exp)
                pos += 1
        except:
            pass
    def getVariableNames(self):
        return [e.getName() for e in self.expressions]
    def getReturnValues(self):
        return [e.getValue() for e in self.expressions]
    def getReturn(self):
        tupleStr = createTupleString( self.getReturnValues() )
        return tupleStr
    def getBody(self):
        return """        yield %s
""" % self.getReturn()

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        for e in self.expressions:
            globalExps.extend(e.getGlobalExpressions())
        return globalExps

class DistinctCommand(SelectCommand):
    NAME = "DISTINCT"
    SHORT_HELP = "DISTINCT exp1 [as name1], exp2 [as name2] ... - generates distinct set of records"
    LONG_HELP = """DISTINCT exp1 [as name1], exp2 [as name2]
DISTINCT '[' name = expression, ... ']' exp1 [as name1], exp2 [as name2]
    This command generates only distinct records out of all produced by previous chains
    Record is consider distinct if at lieast one of its variables is different.
    Space complexity of the chain command is the size of the distinct set of recors
    Second form allows to use some precalculated expressions
"""
    def __init__(self, preparationList=None):
        SelectCommand.__init__(self, preparationList)
    def getStart(self):
        return """
    distincts = set()
"""
    def getBody(self):
        return """
        t = %s
        if not t in distincts:
            distincts.add(t)
            yield t
""" % self.getReturn()


miner_globals.addKeyWord(command="SELECT")
miner_globals.addKeyWord(command="DISTINCT")
miner_globals.addHelpClass(SelectCommand)
miner_globals.addHelpClass(DistinctCommand)


