#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

#
# This file contains definition of lexer and parser for miner language
#

import loggers
import miner_globals
import os.path
import re


# Build the lexer
import ply.lex as lex
import parser

lexer = lex.lex(module = parser.tokens_module)

import ply.yacc as yacc
#lexer = lex.lex(debug=True,debuglog=log)

# If write_tables=0 is not specified
# yacc parser will write down parsing table file to decrease startup
# times next time miner loads
#parser = yacc.yacc(debug=0, write_tables=0)
minerTablesFileName = os.path.join(miner_globals.getHomeDir(), ".minerparsetables")
if miner_globals.runsUnderPypy:
    minerTablesFileName += "_pypy"
minerTablesFileName = os.path.expanduser(minerTablesFileName)
parserObj = yacc.yacc(start="statement", debug=0, errorlog=loggers.compileLog, picklefile=minerTablesFileName, module=parser)
expressionParserObj = yacc.yacc(start="expression", debug=0, errorlog=loggers.expressionCompileLog, picklefile=minerTablesFileName+"-expression", module=parser, check_recursion=0)
 
def parseCommand(command):
    if miner_globals.debugMode:
        loggers.compileLog.info("Compiling %s" % command)
    lexer.begin('INITIAL')
    if miner_globals.debugMode:
        debug = loggers.basicLog
    else:
        debug = 0
    result = parserObj.parse(command, debug=debug)
    if result and miner_globals.debugMode:
        loggers.compileLog.info("Dumping command to execute\n%s" % result.getCommand())
    return result

def normalizeExpression(expressionStr):
    if miner_globals.debugMode:
        loggers.compileLog.info("Compiling %s" % expressionStr)
    lexer.begin('INITIAL')
    if miner_globals.debugMode:
        debug = loggers.basicLog
    else:
        debug = 0
    result = expressionParserObj.parse(expressionStr, debug=debug)
    if result and miner_globals.debugMode:
        loggers.compileLog.info("Dumping normalized expression %s\n" % result.getValue())
    return result.getValue()
    