#
# Copyright Michael Groys, 2012-2014
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

lexer = lex.lex(module = parser.tokens_module, debuglog=loggers.lexLog)

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
parserObj = yacc.yacc(start="statement", debug=0, debuglog=loggers.parseLog, picklefile=minerTablesFileName, module=parser)
expressionParserObj = yacc.yacc(start="expression", debug=0, errorlog=loggers.parseLog, debuglog=loggers.parseLog, picklefile=minerTablesFileName+"-expression", module=parser, check_recursion=0)
 
def parseCommand(command):
    loggers.compileLog.info("Compiling: %s", command)
    lexer.begin('INITIAL')
    result = parserObj.parse(command, debug=loggers.parseLog)
    if result and loggers.compileLogEnabled:
        result.dumplog(loggers.compileLog, context="Dumping command to execute")
    return result

def normalizeExpression(expressionStr):
    loggers.compileLog.info("Compiling: %s", expressionStr)
    lexer.begin('INITIAL')
    result = expressionParserObj.parse(expressionStr, debug=loggers.parseLog)
    if result and loggers.compileLogEnabled:
        loggers.compileLog.info("Dumping normalized expression: %s\n", result.getValue())
    return result.getValue()
    