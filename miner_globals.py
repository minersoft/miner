import sys
import re
import os.path
import collections

from m.keywords import addKeyWord

# name  of logfile for pyreadline if required
pyreadlineLogFile = None
def setPyreadlineLog(aPyreadlineLog):
    global pyreadlineLogFile
    pyreadlineLogFile = aPyreadlineLog

minerBaseDir = ""

# whether to work in debug mode
# in this mode miner compilation log and command parsing log will be created
debugMode = False

# output file used in scripts
outputFileName = None
def setOutputFile(aOutputFileName):
    """Set output file name for use in scripts"""
    global outputFileName
    outputFileName = aOutputFileName

# dictionary of all parameters
scriptParameters = {}
def setScriptParameters(args):
    import miner_version
    global scriptParameters
    global _toolsPath
    i = 1
    freeArgs = []
    for arg in args:
        # check if it is variable
        match = re.match(r"([a-zA-Z]\w*)= *(.*)$", arg)
        if match:
            scriptParameters[match.group(1)] = match.group(2)
        else:
            scriptParameters[str(i)] = arg
            i += 1
            freeArgs.append(arg)
    if outputFileName is not None:
        scriptParameters[">"] = outputFileName
    scriptParameters["*"] = " ".join(freeArgs)
    scriptParameters["#"] = len(freeArgs)
    scriptParameters["[]"] = "["+",".join('"""'+a+'"""' for a in freeArgs)+"]"
    scriptParameters["@"] = " ".join('"'+a+'"' for a in freeArgs)
    scriptParameters["?"] = "0"
    scriptParameters["MINER_VERSION"] = miner_version.version
    scriptParameters["MINER_HOME"] = getHomeDir()
    scriptParameters["TOOLS_PATH"] = getToolsPath()
    scriptParameters["COMMAND_LINE"] = " ".join(('"'+a+'"') for a in sys.argv[1:]) if len(sys.argv)>1 else "" 

def getScriptParameter(name, defaultValue):
    global scriptParameters
    return scriptParameters.get(name, defaultValue)

def setScriptParameter(name, value):
    global scriptParameters
    scriptParameters[name] = value

def removeScriptParameter(name):
    global scriptParameters
    try:
        del scriptParameters[name]
    except:
        pass

def setReturnValue(returnValue):
    setScriptParameter("?", returnValue)

def isScriptParameterDefined(name):
    global scriptParameters
    return name in scriptParameters

def setVerbose(verbose):
    setScriptParameter("verbose", verbose)

# print script usage
# that should be first command and exit
printUsage = False
def setPrintUsage():
    global printUsage
    printUsage = True

if '__pypy__' in sys.builtin_module_names:
    runsUnderPypy = True
else:
    runsUnderPypy = False

extensionToTypeMap = {
}

typeToClassMap = {
}

def addTargetToClassMapping(targetName, istreamClassName, ostreamClassName, description):
    if istreamClassName:
        try:
            iModuleName, className = istreamClassName.rsplit(".", 2)
        except:
            print "Invalid input stream class name: " + istreamClassName
            return False
        
        if iModuleName != "io_targets":
            if not addImportModule(iModuleName, forceReload=False):
                print "Failed to import '%s', target '%s' not defined" % (iModuleName, targetName)
        
    if ostreamClassName:
        try:
            oModuleName, className = ostreamClassName.rsplit(".", 2)
        except:
            print "Invalid output stream class name: " + ostreamClassName
            return False
        
        if oModuleName != "io_targets":
            if not addImportModule(oModuleName, forceReload=False):
                print "Failed to import '%s', target '%s' not defined" % (oModuleName, targetName)
    typeToClassMap[targetName] = (istreamClassName, ostreamClassName, description)

def addExtensionToTargetMapping(extension, targetName):
    extensionToTypeMap[extension] = targetName

def getAllTargetList():
    return typeToClassMap.keys()

def getTargetHelp():
    global extensionToTypeMap
    keys = sorted(typeToClassMap.keys())
    # reverse extension map
    targetToExtension = {}
    for e,t in extensionToTypeMap.iteritems():
        if t in targetToExtension:
            targetToExtension[t] += "," + e
        else:
            targetToExtension[t] = e
    helpTuples = []
    for k in keys:
        helpTuples.append( (k, targetToExtension.get(k, ""), typeToClassMap[k][2]) )
    return helpTuples

def getInputTargetList():
    return [x[0] for x in filter(lambda var: var[1][0], typeToClassMap.iteritems())]

def getOutputTargetList():
    return [x[0] for x in filter(lambda var: var[1][1], typeToClassMap.iteritems())]

_repositoryFilePatterns = {}
def addRepositoryFilePattern(target, extractionPattern, extractionId, archiveSelector=""):
    """Specifies file name formats used to store files of specific type in repository
    extractionId is used to specify matched group to be used in sorting 
    """
    global _repositoryFilePatterns
    #print "set _repositoryFilePatterns[%s] = (%s, %d)" % (target, extractionPattern, extractionId)
    _repositoryFilePatterns[target] = (re.compile(extractionPattern), extractionId, archiveSelector)

_repositoryDefaultFilePattern = (re.compile(r"([^.]+)\."), 1, "")

def getRepositoryFilePattern(target):
    global _repositoryFilePatterns
    global _repositoryDefaultFilePattern
    return  _repositoryFilePatterns.get(target, _repositoryDefaultFilePattern)

importMap = {"io_targets": ["m.io_targets", None],
             "_runtime": ["m._runtime", None],
             "aggregate":["m.aggregate", None],
             }

def addImportModule(name, realName=None, value=None, resolveModule=True, forceReload=True):
    import traceback
    global __needToUpdateCompleter
    #print "Import", name
    if resolveModule:
        path = realName if realName else name
        importedModule = None
        try:
            if name in importMap and importMap[name][1] is not None:
                if forceReload:
                    #print "Reloading module '%s'" % path
                    importedModule = reload(importMap[name][1])
                    importMap[name][1] = importedModule
                else:
                    return True
            else:
                importedModule = __import__(path)
                if (path!=name) and ("." in path):
                    # extract leaf component since import returns root
                    pathComponents = path.split(".")
                    for c in pathComponents[1:]:
                        importedModule = importedModule.__getattribute__(c) 
                    
            importsWereModified()
        except BaseException as e:
            print "Failed to import '%s':\n  %s " % (path, str(e)) 
            traceback.print_exc()
            return False
        else:
            importMap[name] = [realName, importedModule]
            #print "Content of imported", name
            #print dir(importedModule)
    else:
        importMap[name] = [realName, value]
        
    __needToUpdateCompleter = True
    return True

def removeImportModule(path):
    global __needToUpdateCompleter
    try:
        del importMap[path]
        __needToUpdateCompleter = True
    except:
        print "Module %s doesn't exist" % path

def getClassFromImported(importName, className):
    importObj = importMap.get(importName, None)
    if not importObj or not importObj[1]:
        return None
    try:
        return getattr(importObj[1], className)
    except:
        return None

def getImportedModules():
    importedModules = []
    for name, value in importMap.iteritems():
        if value[1]:
            importedModules.append( (name, value[1]) )
    return importedModules

aliasCommands = {}

__helpClasses = []
def addHelpClass(helpClass):
    __helpClasses.append(helpClass)

def getHelpClasses():
    return __helpClasses

allVariables = {}

def setVariable(name, value):
    global __needToUpdateCompleter
    allVariables[name] = value
    __needToUpdateCompleter = True

def removeVariable(name):
    global __needToUpdateCompleter
    try:
        del allVariables[name]
        __needToUpdateCompleter = True
    except:
        print "Variable %s doesn't exist" % name

def getVariable(name):
    return allVariables[name]

__importsWereModified = False

def checkIfImportsWereModified():
    global __importsWereModified
    wereModified = __importsWereModified
    __importsWereModified = False
    return wereModified

def importsWereModified():
    global __importsWereModified
    __importsWereModified = True

__needToUpdateCompleter = False
def needToUpdateCompleter():
    global __needToUpdateCompleter
    if __needToUpdateCompleter:
        __needToUpdateCompleter = False
        return True
    return False

def getHelpClass(commandName):
    for helpClass in __helpClasses:
        if helpClass.NAME == commandName or  helpClass.NAME.startswith(commandName + " "):
            try:
                return helpClass
            except:
                pass
            break
    return None

__completionSymbols = {}
def addCompletionSymbol(name, value):
    __completionSymbols[name] = value

def getSymbolsForCompletion(symbols):
    for name, value in __completionSymbols.iteritems():
        symbols[name] = value
    for name, value in importMap.iteritems():
        symbols[name] = value[1]

__aggregatorMap = {}
__aggregatorImportSet = set()

def addAggregator(name, aggClass, helpText):
    __aggregatorMap[name] = (aggClass, helpText)
    importName, className = aggClass.rsplit(".", 1)
    __aggregatorImportSet.add(importName)

def getAggregators():
    return sorted(__aggregatorMap.keys())

def getAggregatorImports():
    return list(__aggregatorImportSet)

def getAggregatorClass(name):
    aggClassTuple = __aggregatorMap.get(name, None)
    if aggClassTuple:
        return aggClassTuple[0]
    else:
        return name
   
def getAggregatorHelp(name):
    return __aggregatorMap[name][1]

__accumulatorMap = {}

def addAccumulator(varName, accumulatorClassName):
    try:
        moduleName, className = accumulatorClassName.rsplit(".", 2)
    except:
        print "Invalid accumulator class name: " + accumulatorClassName
        return False
    
    if not addImportModule(moduleName, forceReload=False):
        print "Failed to import '%s' for accumulation of %s" % (moduleName, varName)
    __accumulatorMap[varName] = accumulatorClassName

def getAccumulator(varList):
    for var in varList:
        if var in __accumulatorMap:
            return (var, __accumulatorMap[var])
    return None

__parserClassMapping = {}
__parserFunctionMapping = {}

def addParserClassMapping(parserObjectName, parserClassName, description):
    try:
        moduleName, className = parserClassName.rsplit(".", 1)
    except:
        print "Invalid parser class name: " + parserClassName
        return False
    __parserClassMapping[parserObjectName] = (parserClassName, description)
    if not addImportModule(moduleName, forceReload=False):
        print "Failed to import '%s' for parsing %s" % (moduleName, parserObjectName)

def getParserHelp():
    return sorted( (name, value[1]) for name, value in __parserClassMapping.items())

def getParserObjectClass(parserObjectName):
    try:
        return __parserClassMapping[parserObjectName][0]
    except:
        return None

def addParserMapping(parserObjectName, requiredVariableName, parserFunction):
    try:
        moduleName, functionName = parserFunction.rsplit(".", 1)
    except:
        print "Invalid parser function name: " + parserFunction
        return False
    
    if not addImportModule(moduleName, forceReload=False):
        print "Failed to import '%s' for parsing of %s" % (moduleName, parserObjectName)
    if parserObjectName in __parserFunctionMapping:
        __parserFunctionMapping[parserObjectName].append( (requiredVariableName, parserFunction) )
    else:
        __parserFunctionMapping[parserObjectName] = [ (requiredVariableName, parserFunction) ]

def getParserMapping(parserObjectName, varList):
    mappingList = __parserFunctionMapping.get(parserObjectName, None)
    if not mappingList:
        return None
    for t in mappingList:
        if t[0] in varList:
            return t
    return None

def getParserObjects():
    return set(__parserFunctionMapping.keys() + __parserClassMapping.keys())

echoMode = False
def setEchoMode(mode):
    global echoMode
    echoMode = mode

_homeDir = os.path.expanduser("~")
def setHomeDir(path):
    global _homeDir
    _homeDir = os.path.abspath(os.path.expanduser(path))

def getHomeDir():
    global _homeDir
    return _homeDir

_toolsPath = None
def getToolsPath():
    global _toolsPath
    if not _toolsPath:
        _toolsPath = os.path.join(getHomeDir(), "miner-tools")
    return _toolsPath

def getToolPath(toolName):
    return os.path.join(getToolsPath(), toolName)

def setToolsPath(toolsPath):
    global _toolsPath
    _toolsPath = os.path.abspath(os.path.expanduser(toolsPath))
    

_scriptCallStack = collections.deque()
_executeScript = None
lineNumber = 1
def callScript(scriptName, inPrivateEnvironment=False, **additionalParameters):
    global scriptParameters
    global lineNumber
    if len(_scriptCallStack) == 0:
        dirName = "."
    else:
        dirName = os.path.dirname(_scriptCallStack[-1][0])
    if (os.sep not in scriptName) and (not scriptName.endswith(".miner")):
        if scriptName.startswith(".") or ("." not in scriptName):
            # create it relative to parent script
            if scriptName.startswith("."):
                scriptName = scriptName[1:]
                while scriptName.startswith("."):
                    dirName = os.path.join(dirName, "..")
                    scriptName = scriptName[1:]
            toolScriptName = scriptName.replace(".", os.sep)
            toolScriptName += ".miner"
            scriptPath = os.path.join(dirName, toolScriptName)
        else:
            toolName = scriptName.split(".",1)[0]
            useTool(toolName)
            toolScriptName = scriptName.replace(".", os.sep)
            toolScriptName += ".miner"
            scriptPath = os.path.join(getToolsPath(), toolScriptName)
    else:
        scriptName = os.path.expanduser(scriptName)
        if scriptName.startswith(os.sep):
            scriptPath = scriptName
        else:
            scriptPath = os.path.join(dirName, scriptName)
    if inPrivateEnvironment:
        params = dict(scriptParameters.items(), **additionalParameters)
    else:
        params = scriptParameters
    _scriptCallStack.append( (scriptPath, scriptParameters, lineNumber) )
    scriptParameters = params
    try:
        _executeScript(scriptPath)
        return popScriptStack()
    except:
        popScriptStack()
        raise

def popScriptStack():
    global scriptParameters
    global lineNumber
    poped = _scriptCallStack.pop()
    params = poped[1]
    lineNumber = poped[2]
    returnVal = getScriptParameter("?", "0")
    if params is not scriptParameters:
        scriptParameters = params
        # propagate return value
        setReturnValue(returnVal)
    return returnVal

def getCurrentScriptPath():
    if len(_scriptCallStack) == 0:
        return "stdin"
    else:
        return _scriptCallStack[-1][0]

def getScriptLocation(line=0):
    """returns current location in script e.g. file.miner:123"""
    global lineNumber
    filename = getCurrentScriptPath()
    if filename == "stdin":
        return "stdin"
    else:
        if not line:
            line = lineNumber
        return "%s:%d" % (os.path.basename(filename), line)

def getExceptionLocation(line=0):
    """returns location for exception messages, e.g. file.miner:123: """
    location = getScriptLocation(line)
    if location == "stdin":
        return ""
    else:
        return "%s: " % location

def evalExpression(e):
    global allVariables
    globalDict = dict(globals().items() + allVariables.items() + getImportedModules())
    return eval(e, globalDict)

def execExpression(e):
    global allVariables
    globalDict = dict(globals().items() + allVariables.items() + getImportedModules())
    exec(e, globalDict)


_miningHistoryFile = None

def setHistoryFile(historyFile):
    global _miningHistoryFile
    _miningHistoryFile = historyFile

def getHistoryFile():
    global _miningHistoryFile
    if _miningHistoryFile is None:
        return os.path.join(getHomeDir(),".mining-history")
    else:
        return os.path.expanduser(_miningHistoryFile)

getToolVersion = None

_usedTools = set()

def useTool(toolName):
    if toolName in _usedTools:
        #print "'%s' toolbox is already in use" % toolName
        return
        

    location = getToolPath(toolName)
    if not os.path.isdir(location) and not os.path.islink(location):
        print "'%s' toolbox is not installed at %s" % (toolName, location)
        return
    _usedTools.add(toolName)
    sys.path.append(location)
    initScript = os.path.join(location, "init.miner")
    if os.path.isfile(initScript):
        callScript(initScript)

_isInteractive = False

def isInteractive():
    global _isInteractive
    return _isInteractive

def setIsInteractive(aIsInteractive):
    global _isInteractive
    _isInteractive = aIsInteractive

_registry = None
def loadRegistry():
    from m.utilities import loadFromJson, saveToJson
    global _registry
    _registry = loadFromJson(os.path.join(getToolsPath(), "registry.json"))
    if _registry:
        for key, value in _registry.iteritems():
            setScriptParameter(key, str(value))
    else:
        # init with miner warehouse path and save
        _registry = {}
        updateRegistry("MINER_WAREHOUSE", "github:///minersoft/warehouse")

def updateRegistry(name, value):
    from m.utilities import saveToJson
    global _registry
    if _registry is None:
        loadRegistry()
    if not value and (name in _registry):
        del _registry[name]
    else:
        _registry[name] = value
 
    if not os.path.isdir(getToolsPath()):
        os.makedirs(getToolsPath())
                             
    saveToJson(_registry, os.path.join(getToolsPath(), "registry.json"))
    setScriptParameter(name, str(value))

_globalCompletionState = -1

def setGlobalCompletionState(state):
    global _globalCompletionState
    _globalCompletionState = state

def resetGlobalCompletionState():
    global _globalCompletionState
    _globalCompletionState = -1

def getGlobalCompletionState():
    global _globalCompletionState
    return _globalCompletionState
