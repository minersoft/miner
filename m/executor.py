#
# Copyright Michael Groys, 2012-2014
#

#
# This file provides implementation of main execute command function
#

import compiler
import traceback
import common
import sys
import re
import string
import loggers
import os
import miner_globals
import collections 
import register_builtins
import time

# debug mode if enable parser and compilation log files are created
def setDebugMode(debugMode):
    if debugMode:
        loggers.setDebugMode()
    miner_globals.debugMode = debugMode

class ParameterSubstitutor(string.Template):
    idpattern = r"[0-9>*?]|[a-zA-Z][_a-zA-Z0-9]*|\#|\[\]"
    def __init__(self, command):
        string.Template.__init__(self, command)

    def update(self):
        return self.safe_substitute(miner_globals.scriptParameters)

def substituteLine(line):
    substitutor = ParameterSubstitutor(line)
    return substitutor.update()

def createAliases(aliases):
    if not aliases:
        return
    for a in aliases:
        execute("ALIAS %s" % a, verbose=False)

def createVariables(variables):
    if not variables:
        return
    for v in variables:
        execute("SET %s" % v, verbose=False)

def createImports(imports):
    if not imports:
        return
    for i in imports:
        execute("IMPORT %s" % i, verbose=False)

def createUses(uses):
    if not uses:
        return
    for i in uses:
        execute("USE %s" % i, verbose=False)

def executeCommands(commands, verbose=True):
    if not commands:
        return
    for c in commands:
        execute(c, verbose)

_gScriptPath = []

def setScriptPath(scriptPath):
    global _gScriptPath
    _gScriptPath = _gScriptPath

def executeScript(scriptFileName):
    scriptFH = None
    try:
        if os.path.exists(scriptFileName):
            scriptFH = open(scriptFileName, "r")
        else:
            for fileName in [os.path.join(e,scriptFileName) for e in _gScriptPath]:
                if os.path.exists(fileName):
                    scriptFH = open(fileName, "r")
    except:
        print "Failed to open %s" % scriptFileName
        traceback.print_exc()
        return
    if not scriptFH:
        print "Script %s was not found" % scriptFileName
        return

    lines = []
    lineNumber = 1
    while True:
        line = scriptFH.readline()
        if not line:
            break
        line = line.rstrip('\n')
        if line == "":
            lineNumber += 1
            continue
        # check if span to multiple lines
        while line[-1] == "\\" or line[-1] == "|":
            contLine = scriptFH.readline()
            contLine = contLine.rstrip('\n')
            if contLine=="":
                break
            if len(line)>=1 and line[-1] == "\\":
                line = line[0:-1]
            line += contLine
            lineNumber += 1
        lines.append( (lineNumber, line) )
        lineNumber += 1

    scriptFH.close()
    try:
        executeLines( (lineTuple for lineTuple in lines) )
    except common.ReturnFromScript:
        return

    
def executeLines(linesGenerator):
    for lineNumber, line in linesGenerator:
        tokens = line.split(None, 1)
        if len(tokens) >= 1:
            if tokens[0] == "if":
                if len(tokens) != 2:
                    print >>sys.stderr, "%sInvalid if command: '%s'" % (miner_globals.getExceptionLocation(line=lineNumber), line)
                    continue
                processIf(lineNumber, tokens[1], linesGenerator)
                continue
            elif tokens[0] == "for":
                if len(tokens) != 2:
                    print >>sys.stderr, "%sInvalid for command: '%s'" % (miner_globals.getExceptionLocation(line=lineNumber), line)
                    continue
                processFor(lineNumber, tokens[1], linesGenerator)
                continue
            elif tokens[0] == "fi":
                continue
            elif tokens[0] in ["echo", "@echo"]:
                executeEcho(tokens)
                continue
            elif tokens[0] == "sleep":
                executeSleep(lineNumber, tokens[1])
                continue
        execute(line, isBatch=True, lineNumber=lineNumber)

def evalExpression(e, lineNumber=0):
    try:
        normalized = compiler.normalizeExpression(e)
        res = miner_globals.evalExpression(normalized)
    except common.CompilerSyntaxError as exc:
        print "%sCompilation error for: '%s'\n%s" % (miner_globals.getExceptionLocation(line=lineNumber),e,str(exc))
        miner_globals.setReturnValue("-999")
        raise common.ReturnFromScript
    except (RuntimeError, TypeError, NameError) as e:
        print miner_globals.getExceptionLocation()+str(e)
        miner_globals.setReturnValue("-999")
        raise common.ReturnFromScript
    except:
        print miner_globals.getExceptionLocation(line=lineNumber)
        traceback.print_exc()
        miner_globals.setReturnValue("-999")
        raise common.ReturnFromScript
    return res
    
def checkIfExpression(e, lineNumber=0):
    #print "e=", e
    if "$?" in e:
        e = re.sub(r'\$\?([_a-zA-Z][_a-zA-Z0-9]*|\>|[0-9])',r'runtime.isParameterDefined("\1")', e)
    e = substituteLine(e)
    res = evalExpression(e, lineNumber=lineNumber)
        
    return True if res else False

def processIf(lineNumber, expStr, linesGenerator):
    #print "processIf", expStr
    isTrue = checkIfExpression(expStr, lineNumber=lineNumber)
    if isTrue:
        runIter = getIfClause(linesGenerator)
        executeLines(runIter)
    else:
        elseLineNumber, tokens, runIter = getElseClause(linesGenerator)
        if len(tokens)==2 and tokens[0]=="elif":
            processIf(elseLineNumber, tokens[1], runIter)
        else:
            executeLines(runIter)
    
def getIfClause(linesGenerator):
    ifCnt = 1
    accumulated = []
    isAccumulating = True
    fiWasFound = False
    for lineNumber, line in linesGenerator:
        #print "getIfClause:", line
        tokens = line.split(None, 1)
        if len(tokens) > 0:
            if tokens[0] == "if":
                ifCnt += 1
            elif tokens[0] in ["else", "elif"] and isAccumulating==True and ifCnt==1:
                isAccumulating = False
            elif tokens[0] == "fi":
                ifCnt -= 1
                if ifCnt == 0:
                    accumulated.append( (lineNumber, "fi") )
                    fiWasFound = True
                    break
            if isAccumulating:
                #print "getIfClause accumulating:", line
                accumulated.append( (lineNumber, line) )
    if not fiWasFound:
        #print >>sys.stderr, ("End of if was not found")
        sys.exit(1)
    return (lineTuple for lineTuple in accumulated)
        
def getElseClause(linesGenerator):
    ifCnt = 1
    accumulated = []
    isAccumulating = False
    fiWasFound = False
    elseTokens = []
    elseLineNumber = 0
    for lineNumber,line in linesGenerator:
        #print "getElseClause", line
        tokens = line.split(None, 1)
        if len(tokens) > 0:
            if isAccumulating:
                #print "getElseClause accumulating:", line
                accumulated.append( (lineNumber, line) )
            if tokens[0] == "if":
                ifCnt += 1
            elif tokens[0] in ["else", "elif"] and isAccumulating==False and ifCnt == 1:
                elseLineNumber = lineNumber
                elseTokens = tokens
                isAccumulating = True
            elif tokens[0] == "fi":
                ifCnt -= 1
                if ifCnt == 0:
                    accumulated.append((lineNumber, "fi"))
                    fiWasFound = True
                    break
        
    if not fiWasFound:
        #print >>sys.stderr, ("End of if was not found")
        sys.exit(1)
    #print "getElseClause accumulated:", accumulated
    return (elseLineNumber, elseTokens, (lineTuple for lineTuple in accumulated))

def getListExpression(e, lineNumber=0):
    res = evalExpression(e, lineNumber=lineNumber)
    if not isinstance(res, list):
        print "%s'%s' should evaluate to list" % (miner_globals.getExceptionLocation(line=lineNumber),e)
        raise common.ReturnFromScript
    return res

def getForBody(linesGenerator):
    return getBlockBody(linesGenerator, "for", "done")

def getBlockBody(linesGenerator, blockStart, blockEnd):
    startCounter = 1
    accumulated = []
    for lineNumber,line in linesGenerator:
        tokens = line.split(None, 1)
        if len(tokens) > 0:
            if tokens[0]==blockStart:
                startCounter+=1
            elif tokens[0]==blockEnd:
                startCounter -= 1
                if startCounter == 0:
                    break
            accumulated.append( (lineNumber,line) )
    return accumulated


def processFor(lineNumber, forCommand, linesGenerator):
    forCommand = substituteLine(forCommand)
    try:
        paramName, inStr, listExpression = forCommand.split(None, 2)
        if inStr != "in":
            raise RuntimeError("in")
    except:
        print >>sys.stderr, "%sInvalid for command 'for %s'\nShould be: for <paramName> in <listExpression>" % (miner_globals.getExceptionLocation(line=lineNumber), forCommand)
        raise common.ReturnFromScript
    
    forBody = getForBody(linesGenerator)
    paramListValues = getListExpression(listExpression, lineNumber=lineNumber)
    for paramValue in paramListValues:
        miner_globals.setScriptParameter(paramName, paramValue)
        executeLines( (lineTuple for lineTuple in forBody) )

ECHO_REDIRECT_REGEXP = re.compile("^(\>?)(\>|\>&) *([-.,/_0-9a-zA-Z~+]+) *$")
def executeEcho(tokens):
    if len(tokens) > 1:
        s = substituteLine(tokens[1])
    else:
        s = ""
    if miner_globals.echoMode and tokens[0] != "@echo":
        print ">>>", "echo", s
    if s == "on":
        miner_globals.setEchoMode(True)
        return
    elif s == "off":
        miner_globals.setEchoMode(False)
        return
    elif s == "push":
        pushRedirect()
        return
    elif s == "pop":
        popRedirect()
        return
    else:
        match = ECHO_REDIRECT_REGEXP.match(s)
        if match:
            redirectOutput(match.group(3), appendMode=(match.group(1)==">"), includeStderr=(match.group(2)==">&"))
            return
    print s

_redirectFile = None
def redirectOutput(fileName, appendMode=False, includeStderr=False):
    global _redirectFile
    _redirectFile = open(fileName, "a" if appendMode else "w")
    os.dup2(_redirectFile.fileno(), sys.stdout.fileno())
    if includeStderr:
        # reopen files without buffering
        sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)
        os.dup2(_redirectFile.fileno(), sys.stderr.fileno())

_redirectStack = collections.deque()
def pushRedirect():
    global _redirectFile
    pushDict = {}
    pushDict["redirect"] = _redirectFile
    pushDict["stdout"] = sys.stdout
    pushDict["stderr"] = sys.stderr
    pushDict["stdoutFH"] = os.dup(sys.stdout.fileno())
    pushDict["stderrFH"] = os.dup(sys.stderr.fileno())
    _redirectStack.append(pushDict)

def popRedirect():
    global _redirectFile
    if len(_redirectStack) == 0:
        print "No redirects in stack"
        return
    if _redirectFile:
        _redirectFile.close()
    pushDict = _redirectStack.pop()
    _redirectFile = pushDict["redirect"]
    sys.stdout = pushDict["stdout"]
    sys.stderr = pushDict["stderr"]
    os.dup2(pushDict["stdoutFH"], sys.stdout.fileno())
    os.dup2(pushDict["stderrFH"], sys.stderr.fileno())
    os.close(pushDict["stdoutFH"])
    os.close(pushDict["stderrFH"])

def executeSleep(lineNumber, intervalStr):
    intervalStr = substituteLine(intervalStr)
    try:
        interval = float(intervalStr)
    except:
        print >>sys.stderr, "%ssleep interval should be float: '%s'" % (miner_globals.getExceptionLocation(line=lineNumber), intervalStr)
    time.sleep(interval)
def printDoc(idStr):
    from statements.doc_statement import DocStatement
    try:
        stmt = DocStatement(idStr)
        stmt.execute()
    except:
        print "Invalid id - " + idStr
    
def printHelp(idStr):
    from statements.help_statement import Help
    Help.printHelp(idStr)

def execute(command, verbose=True, isBatch=False, scriptFileName="stdin", lineNumber=0):
    '''
    Main execute function
    '''
    if not command:
        return
    miner_globals.lineNumber = lineNumber
    command = command.strip()
    # pound is miner's comment as well
    if command=="" or command[0] =="#":
        return
    if '$' in command:
        # substitute parameters
        command = substituteLine(command)

    if miner_globals.echoMode:
        print ">>>", command
    result = None
    try:
        result = compiler.parseCommand(command)
        if not result:
            return
        try:
            result.execute()
        except KeyboardInterrupt:
            print "Execution aborted"
    except common.CompilerSyntaxError as err:
        offset = err.offset
        if offset < 0:
            offset = len(command)
        startVisualOffset = int(offset/60) * 60
        print "%sSyntax Error at:" % miner_globals.getExceptionLocation()
        print command[startVisualOffset:startVisualOffset+60]
        print "-"*(offset-startVisualOffset) + "^"
        miner_globals.setReturnValue("-999")
    except common.InvalidInputFiles as err:
        print "%sInvalid input file(s): %s" % (miner_globals.getExceptionLocation(), str(err))
        miner_globals.setReturnValue("-1")
    except common.OutputException as err:
        print "%sInvalid output command: %s" % (miner_globals.getExceptionLocation(), str(err))
        miner_globals.setReturnValue("-2")
    except common.CompilationError as err:
        print "%sCompilation Error: %s" % (miner_globals.getExceptionLocation(), str(err))
        miner_globals.setReturnValue("-3")
    except IOError as err:
        print str(err)
        miner_globals.setReturnValue("-4")
    except common.MiningError as err:
        print "%sError happened during mining: %s" % (miner_globals.getExceptionLocation(), str(err))
        miner_globals.setReturnValue("-5")
    except SystemExit as e:
        sys.exit(e)
    except common.ReturnFromScript:
        if isBatch:
            raise
        else:
            sys.exit()
    except:
        print >>sys.stderr, "%sException occured" % miner_globals.getExceptionLocation()
        print >>sys.stderr, "==================="
        if result:
            print >>sys.stderr, "Prepared code:"
            result.dump(sys.stdout)
        traceback.print_exc()
        print "-----------------"
        miner_globals.setReturnValue("-666")

