#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

import miner_globals
from base import *

def p_command_pass_command(p):
    '''command : pass_command'''
    p[0] = p[1]

def p_pass_command_empty(p):
    '''command : PASS '''
    p[0] = PassCommand()

def p_destination_pass_command(p):
    '''destination : pass_command'''
    p[0] = p[1]

def p_destination_pass_command_empty(p):
    '''destination : PASS '''
    p[0] = PassCommand()

def p_pass_command(p):
    '''pass_command : PASS expression
                    | PASS assign_expression'''
    p[0] = PassCommand()
    p[0].add(p[2])

def p_pass_command_preparation(p):
    '''pass_command : PASS '[' named_parameter_list ']' expression
                    | PASS '[' named_parameter_list ']' assign_expression'''
    p[0] = PassCommand(p[3])
    p[0].add(p[5])

def p_pass_command_expression(p):
    '''pass_command : pass_command ',' expression
                    | pass_command ',' assign_expression'''
    p[0] = p[1]
    p[0].add(p[3])

def p_pass_if_command(p):
    '''pass_command : PASS expression IF expression
                    | PASS assign_expression IF expression'''
    p[0] = PassCommand()
    p[0].add(p[2], p[4])

def p_pass_if_command_preparation(p):
    '''pass_command : PASS '[' named_parameter_list ']' expression IF expression
                    | PASS '[' named_parameter_list ']' assign_expression IF expression'''
    p[0] = PassCommand(p[3])
    p[0].add(p[5], p[7])

def p_pass_command_if_expression(p):
    '''pass_command : pass_command ',' expression IF expression
                    | pass_command ',' assign_expression IF expression'''
    p[0] = p[1]
    p[0].add(p[3], p[5])


class PassCommand(TypicalCommand):
    NAME = "PASS"
    SHORT_HELP = "PASS <expression> [IF <condition>] [, ...] - executes expressions"
    LONG_HELP = """PASS <expression>[, ...]
PASS <expression> IF <condition> [, ...]
PASS <assignment-expression> [IF <condition>]
    PASS is used to execute expressions (e.g. imported functions)
    that don't modify record variables explicitly (Although they can do it via assignment form.
    For example:
      PASS my_module.count(), recordVariable += 10, globalVariable[id] = recordVariable IF recordVariable is not None
    
"""
    def __init__(self):
        TypicalCommand.__init__(self, preparationList = None)
        self.myExpressionList = []
    def add(self, exp, ifExp=None):
        self.myExpressionList.append( (exp, ifExp) )
    def getVariableNames(self):
        return self.myParent.getVariableNames()

    def getStart(self):
        s = ""
        for v in miner_globals.allVariables.keys():
            s += "    global %s\n" % v
        return s

    def getBody(self, dontYield=False):
        s = ""
        for (exp, ifExp) in self.myExpressionList:
            if ifExp:
                s += "        if %s:\n    " % ifExp.getValue()
            s += "        %s\n" % exp.getValue()
        if s == "":
            s += "        pass\n"
        if not dontYield:
            s += "        yield %s" % createTupleString(self.getVariableNames())
        return s

    def createSaver(self, saverName, generatorName):
        s = """
def %s():
%s
    for %s in %s():
%s
""" % (saverName, self.getStart(), createTupleString(self.myParent.getVariableNames()), generatorName, self.getBody(dontYield=True))
        return s

    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        for (exp,ifExp) in self.myExpressionList:
            globalExps += exp.getGlobalExpressions()
            if ifExp:
                globalExps += ifExp.getGlobalExpressions()
        return globalExps

miner_globals.addHelpClass(PassCommand)
miner_globals.addCommandName("PASS")

