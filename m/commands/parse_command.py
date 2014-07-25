#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
import m.common as common
from base import *

####
# parse commands
####

def p_parse_command(p):
    '''command : parse_command'''
    p[0] = p[1]

def p_parse_command_simple(p):
    '''parse_command : PARSE ID'''
    p[0] = ParseCommand()
    p[0].addParserObject(p[2])

def p_parse_command_from(p):
    '''parse_command : PARSE ID FROM expression'''
    p[0] = ParseCommand()
    p[0].addParserObject(p[2], p[4])

def p_parse_command_from_as(p):
    '''parse_command : PARSE ID FROM expression AS ID'''
    p[0] = ParseCommand()
    p[0].addParserObject(p[2], p[4], p[6])

def p_parse_command_parse_simple(p):
    '''parse_command : parse_command ',' ID'''
    p[0] = p[1]
    p[0].addParserObject(p[3])

def p_parse_command_parse_from(p):
    '''parse_command : parse_command ',' ID FROM expression'''
    p[0] = p[1]
    p[0].addParserObject(p[3], p[5])

def p_parse_command_parse_from_as(p):
    '''parse_command : parse_command ',' ID FROM expression AS ID'''
    p[0] = p[1]
    p[0].addParserObject(p[3], p[5], p[7])

####
# Implementation
####

class ParseCommand(TypicalCommand):
    NAME = "PARSE"
    SHORT_HELP = "PARSE <id> [FROM <expression>]"
    @staticmethod
    def COMPLETION_STATE(input, pos):
        return  sorted(miner_globals.getParserObjects()) + ["FROM", "AS"]
    @staticmethod
    def LONG_HELP():
        s  = """PARSE <id>
PARSE <id> FROM <expression> [as <name>]
    Parses object specified by <id>. Source of object (e.g. URI string is either determined
    automatically from the available variables) or from the FROM expression provided.
    AS can be used to give different name for extracted object
    Multiple parse directives can be defined at the same time, e.g.
      PARSE request, l2tol4 FROM coal.flow.L2toL4ClientSyn, l2tol4 FROM coal.flow.L2toL4ClientFirstPayload as l2tol4payload 
    <id> can be one of:
"""
        parserHelp = miner_globals.getParserHelp()
        for helpTuple in parserHelp:
            s += "      %-10s - %s\n" % (helpTuple[0], helpTuple[1])
        return s
    def __init__(self):
        TypicalCommand.__init__(self)
        # parser objects is list of triplets: (parserObjectNames, fromExpression, asName)
        self.parserObjects = []
    
    def addParserObject(self, parserObjectName, fromExpression=None, asName=None):
        if not asName:
            asName = parserObjectName
        self.parserObjects.append( (parserObjectName, fromExpression, asName) )
        
    def getParserString(self, parserObjectName, fromExpStr, asName):
        parserObjectClassName = miner_globals.getParserObjectClass(parserObjectName)
        if not parserObjectClassName:
            raise common.CompilationError("Unknown parser object: %s" % parserObjectName)
        if fromExpStr:
            return "        %s = %s(%s)\n" % (asName, parserObjectClassName, fromExpStr)
        else:
            parseTuple = miner_globals.getParserMapping(parserObjectName, self.myParent.getVariableNames())
            if not parseTuple:
                raise common.CompilationError("Failed to find variable to parse '%s' out of [%s]" % (self.parserObjectName, ", ".join(self.myParent.getVariableNames())) )
            return "        %s = %s(%s)\n" % (asName, parseTuple[1], parseTuple[0])
        
    def getBody(self):
        s = ""
        for (parserObjectName, fromExpression, asName) in self.parserObjects:
            s += self.getParserString(parserObjectName, fromExpression.getValue() if fromExpression else None, asName)
        s += """
        yield %s
""" % (createTupleString(self.getVariableNames()),)
        return s

    def getVariableNames(self):
        parserVariableNames = []
        for (parserObjectName, fromExpression, asName) in self.parserObjects:
            parserVariableNames.append(asName)
        return self.myParent.getVariableNames() + parserVariableNames

    def getGlobalExpressions(self):
        globalExpressions = []
        for (parserObjectName, fromExpression, asName) in self.parserObjects:
            if fromExpression:
                globalExpressions += fromExpression.getGlobalExpressions()
        return globalExpressions

####
# completion symbols
####
miner_globals.addHelpClass(ParseCommand)
miner_globals.addCommandName("PARSE")

