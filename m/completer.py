import sys
import miner_globals
import os.path
import glob
import os
import traceback

if sys.platform.startswith("win") or miner_globals.runsUnderPypy:
    # on windows platform or under pypy
    import readline_replacement as readline
    sys.modules['readline'] = readline
else:
    import readline

import rlcompleter
import types
import common
from m.commands import SOURCE_COMMAND_NAMES, DESTINATION_COMMAND_NAMES
import repository_path

pythonReserved = set(["if", "else", "elif", "import", "def", "class", "try", "while", "with", "raise", "yield", "return",
"pass", "break", "continue", "finally", "except", "global"])

class CompleterWrap(rlcompleter.Completer):
    """
    Complete symbols and defined variables
    """
    def __init__(self):
        tmpSymbols = dict()
        miner_globals.getSymbolsForCompletion(tmpSymbols)
        symbols = dict(tmpSymbols.items() + miner_globals.allVariables.items())
        # Create dummy objects for completion
        rlcompleter.Completer.__init__(self, symbols)
        self.noMore = False
        self.parentState = 0
        self.matchedVars = []
        self.helpClass = None

    def setHelpClass(self, helpClass):
        self.helpClass = helpClass

    def complete(self, text, state):
        if state == 0:
            self.noMore = False
            self.parentState = 0
            # statements is a list of (name, value) tuples, we need only the names
            varsToFilter = ["True", "False", "None"]
            if self.helpClass:
                try:
                    varsToFilter += common.HelpClass.getMoreSymbolsForCompletion(self.helpClass)
                except Exception as e:
                    print e
            #print varsToFilter
            self.matchedVars = filter(lambda var: var.startswith(text), sorted(varsToFilter))
        if state<len(self.matchedVars):
            return self.matchedVars[state]
        while not self.noMore:
            completion = rlcompleter.Completer.complete(self, text, self.parentState)
            if not completion:
                self.noMore = True
            else:
                self.parentState += 1
                if completion.find("._") == -1 and (completion not in pythonReserved) and (not completion.endswith("_FIELD_NUMBER")):
                    return completion
        return None

theSymbolCompleter = CompleterWrap()

def symbolCompleter(text, state):
    global theSymbolCompleter

    if state==0 and miner_globals.needToUpdateCompleter():
        helpClass = theSymbolCompleter.helpClass;
        theSymbolCompleter = CompleterWrap()
        theSymbolCompleter.setHelpClass(helpClass)

    try:
        return theSymbolCompleter.complete(text, state)
    except:
        return None

_competionsList = []
def completeFromList(text, state, itemsList):
    global _competionsList
    if state==0:
        if isinstance(itemsList, types.FunctionType):
            itemsList = itemsList()
        _competionsList = sorted(filter(lambda c: c.startswith(text), itemsList))
    return _competionsList[state]

currentCompletionState = common.COMPLETE_NONE

def myCompleterFunc(text, state):
    global currentCompletionState
    if state == 0:
        currentCompletionState = getCompletionState()
    if currentCompletionState == common.COMPLETE_FILE:
        return fileCompleter(text, state)
    elif currentCompletionState == common.COMPLETE_SYMBOLS:
        return symbolCompleter(text, state)
    elif currentCompletionState == common.COMPLETE_COMMANDS:
        return completeFromList(text, state, commandsForCompletion + miner_globals.aliasCommands.keys())
    elif currentCompletionState == common.COMPLETE_STATEMENTS:
        return completeFromList(text, state, statementsForCompletion)
    elif currentCompletionState == common.COMPLETE_FOR_HELP:
        return completeFromList(text, state, helpTopicsForCompletion)
    elif currentCompletionState == common.COMPLETE_TOOLS:
        return completeFromList(text, state, getToolsList)
    elif currentCompletionState == common.COMPLETE_REPOSITORY:
        return repositoryFileCompleter(text, state)
    elif currentCompletionState == common.COMPLETE_IMPORT:
        return importPathCompleter(text, state)
    elif currentCompletionState == common.COMPLETE_TARGET:
        return completeFromList(text, state, miner_globals.getAllTargetList)
    elif isinstance(currentCompletionState, list):
        return completeFromList(text, state, currentCompletionState)
    elif isinstance(currentCompletionState, types.FunctionType):
        return completeFromList(text, state, currentCompletionState)
    else:
        return None

readline.set_completer(myCompleterFunc)

# There are number different completion states:
# 1. if we are inside string - completion is disabled
# 2. if it is first command - Treat it as statement or "READ"
# 3. If first word after PIPE -> command or "WRITE"
# 4. If after HELP can by any
# 5. If after READ or write -> FILE
# 6. Otherwise -> symbols or variables


def getCompletionState():
    """
    Determine completion state according to the current readline global state
    """
    line = readline.get_line_buffer()
    beginIndex = readline.get_begidx()
    endIndex = readline.get_endidx()
    # check if we are in string (only double quotes are considered)
    inString = False
    position = 0
    countBackspaces = 0
    while position<beginIndex:
        if line[position] == '"' and countBackspaces%2==0:
            inString = not inString
            countBackspaces = 0
        elif inString and line[position] == '\\':
            countBackspaces += 1
        else:
            countBackspaces = 0
        position += 1
    if inString:
        return common.COMPLETE_NONE
    start = endIndex-1
    while start>=0:
        if line[start]=='|' or line[start]=='{' or line[start]=='}':
            break
        start -= 1
    start += 1
    if start == 0:
        firstCommand = True
    else:
        firstCommand = False
    while start < beginIndex and line[start].isspace():
        start += 1
    if start == beginIndex:
        # We are on the first word
        if firstCommand:
            return common.COMPLETE_STATEMENTS
        else:
            return common.COMPLETE_COMMANDS

    position = start
    while position < beginIndex and line[position].isalpha():
        position += 1

    # check if first command in the load or save then we want to complete files
    command = line[start:position]
    helpClass = miner_globals.getHelpClass(command)
    theSymbolCompleter.setHelpClass(helpClass)
    if helpClass:
        state = common.HelpClass.getCompletionState(helpClass)
        if state == common.COMPLETE_FILE:
            # check if it is complete tartget
            while position < beginIndex and line[position].isspace():
                position += 1
            if position<beginIndex and line[position] =='<':
                position += 1
                while position < beginIndex and (line[position].isalnum() or line[position]=='_'):
                    position += 1
                if position == beginIndex:
                    state = common.COMPLETE_TARGET
        return state
    else:
        return common.COMPLETE_NONE


class FileCompleter:
    """
    Implements file completer
    """
    def __init__(self, prefixParameterName=None, directoriesOnly=False, globExp="*", updateBuffer=True):
        self.prefixParameterName = prefixParameterName
        self.defaultPrefix = ""
        self.completions = []
        self.directoriesOnly = directoriesOnly
        self.globExp = globExp
        self.updateBuffer = updateBuffer
    def getFileName(self):
        line = readline.get_line_buffer()
        endIndex = readline.get_endidx()
        # get the filename to complete
        position = readline.get_begidx()
        while position > 0:
            position -= 1
            if line[position] in u' \t\n':
                position += 1
                break
        return line[position:endIndex]
    def getCompletions(self, text):
        # This function is called once when TAB is preseed
        text = self.calcPathFromText(text)
        completions = map(os.path.basename, glob.glob(text + self.globExp))
        self.completions = []
        fileDir = os.path.dirname(text)
        basenameText = os.path.basename(text)
        # mark all directories with slash at the end
        for f in completions:
            if os.path.isdir(os.path.join(fileDir,f)):
                self.completions.append(f + os.sep)
            elif not self.directoriesOnly:
                self.completions.append(f)

        if not self.updateBuffer:
            return self.completions
        if len(self.completions) == 0:
            self.completions = []
        elif len(self.completions) == 1:
            # if there is only one completion - insert left text as is
            readline.insert_text(self.completions[0][len(basenameText):])
            # if completion is a file add space at the end
            if not self.completions[0].endswith(os.path.sep):
                readline.insert_text(" ")
            self.completions = []
        else:
            # Try to find common prefix
            commonPrefix = os.path.commonprefix(completions)
            if len(os.path.join(fileDir,commonPrefix)) > len(text):
                # add common suffix
                substruct = 0 if not fileDir else (len(fileDir)+1)
                readline.insert_text(commonPrefix[len(text) - substruct:])
                self.completions = []
            else:
                # add empty string to avoid auto completion
                self.completions.append(" ")
        return self.completions
    def calcPathFromText(self, text):
        if self.prefixParameterName:
            prefix = miner_globals.getScriptParameter(self.prefixParameterName, "")
        else:
            prefix = self.defaultPrefix
        path = prefix + text
        path = os.path.expanduser(path)
        return path
        
    def complete(self, text, state):
        if state == 0:
            self.getCompletions(self.getFileName())
        return self.completions[state]

fileCompleter = FileCompleter().complete

class RepositoryFileCompleter(FileCompleter):
    def __init__(self):
        FileCompleter.__init__(self, directoriesOnly=True)
        self.repositoryPathObj = None
        self.targetList = None
    def calcPathFromText(self, text):
        return self.repositoryPathObj.expand(text)
    def complete(self, text, state):
        text=self.getFileName()
        if state == 0:
            self.repositoryPathObj = repository_path.RepositoryPath()
        
        if "/" in text:
            return FileCompleter.complete(self, text, state)
        else:
            # Explicit insert to support file word separator
            if state == 0:
                self.completions = []
                self.targetList = [t+"/" for t in self.repositoryPathObj.getTargetList()]
                self.targetList = filter(lambda var: var.startswith(text), sorted(self.targetList))
                if len(self.targetList) == 0:
                    return None
                elif len(self.completions) == 1:
                    # if there is only one completion - insert left text as is
                    readline.insert_text(self.targetList[0][len(text):])
                commonPrefix = os.path.commonprefix(self.targetList)
                if len(commonPrefix) > len(text):
                    readline.insert_text(commonPrefix[len(text):])
                    self.targetList.append(" ")
            return self.targetList[state]

repositoryFileCompleter = RepositoryFileCompleter().complete

class ImportPathCompleter:
    def __init__(self):
        self.completionList = []
        self.parentPath = None
        self.fileCompleter = FileCompleter(globExp="*.py", updateBuffer=False)
        self.dirCompleter = FileCompleter(directoriesOnly=True, updateBuffer=False)
    def extractParentPath(self, importName):
        for path in sys.path:
            if os.path.isdir(os.path.join(path, importName)):
                return path
        return None
    def complete(self, text, state):
        try:
            text = self.fileCompleter.getFileName()
            if state == 0:
                self.completions = self.getCompletions(text)
        except:
            traceback.print_exc()
            raise IndexError()
        return self.completions[state]
            
    def getCompletions(self, text):
        if "." not in text:
            return self.getTopLevelCompletions(text)
        else:
            parentPath = self.extractParentPath(text.split(".",1)[0])
            #print "parentPath", parentPath
            if not parentPath:
                return []
            return self.getNodeCompletions(text, parentPath)
    def getNodeCompletions(self, text, parentPath):
        self.fileCompleter.defaultPrefix = parentPath + "/"
        self.dirCompleter.defaultPrefix = parentPath + "/"
        fileText = text.replace(".", "/")
        dirs = self.dirCompleter.getCompletions(fileText)
        files = [f.replace(".py", "") for f in self.fileCompleter.getCompletions(fileText)]
        files = filter(lambda file: file!= "__init__", files)
        
        completions = sorted(dirs+files)
        completions = [ c.replace("/", ".") for c in completions]
        textFragments = text.rsplit(".", 1)
        if len(textFragments) == 2:
            completions = [(textFragments[0]+"."+c) for c in completions]
        return completions
    def getTopLevelCompletions(self, text):
        completions = []
        for path in sys.path:
            completions += self.getNodeCompletions(text, path)
        return sorted(completions)

importPathCompleter = ImportPathCompleter().complete

statementsForCompletion = miner_globals.getStatementNames() + SOURCE_COMMAND_NAMES
commandsForCompletion = miner_globals.getCommandNames() + DESTINATION_COMMAND_NAMES
helpTopicsForCompletion = statementsForCompletion + commandsForCompletion

def isTool(name):
    fileName = os.path.join(miner_globals.getToolsPath(), name)
    return os.path.isdir(fileName)

def getToolsList():
    try:
        fileNames = os.listdir(miner_globals.getToolsPath())
    except:
        return []
    return filter(isTool, fileNames)
