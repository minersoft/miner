#
# Copyright Qwilt, 2012
#
# The code contained in this file may not be used by any other entities without explicit written permission from Qwilt.
#
# Author: michaelg
# 

#
# This file contains definition of basic Generator interface
# And all Exceptions
#

class GeneratorBase:
    def __init__(self):
        self.myParent = None
    def setParent(self, parent):
        self.myParent = parent
    def getVariableNames(self):
        raise NotImplementedError
    STATIC_VARIABLE_NAMES = None

# Exception types
class InvalidInputFiles(Exception):
    pass

class UnknownDataProvider(InvalidInputFiles):
    def __init__(self, dataProviderName):
        self.dataProviderName = dataProviderName
    def __str__(self):
        return "Unknown data provides %s" % self.dataProviderName

class NoFilesSpecified(InvalidInputFiles):
    def __str__(self):
        return "No files specified"

class NoFilesInPattern(InvalidInputFiles):
    def __init__(self, fileNamePatterns):
        self.myFileNamePatterns = fileNamePatterns
    def __str__(self):
        return "Pattern(s) %s doesn't match any files" % self.myFileNamePatterns

class InvalidPattern(InvalidInputFiles):
    def __init__(self, msg):
        self.myMessage = msg
    def __str__(self):
        return "InvalidPattern(s): %s" % self.myMessage

class InvalidRepositoryPath(InvalidInputFiles):
    def __init__(self, paths):
        self.myPaths = paths
    def __str__(self):
        return "Invalid Repository path(s) specified: %s" % (" ".join(self.myPaths))

class UnknownExtensionType(InvalidInputFiles):
    def __init__(self, fileName):
        self.myFileName = fileName
    def __str__(self):
        return "Unsupported extension '%s'" % self.myFileName

class UnknownTarget(InvalidInputFiles):
    def __init__(self, targetName):
        self.myTargetName = targetName
    def __str__(self):
        return "Unsupported target '%s'" % self.myTargetName

class NoInputStream(InvalidInputFiles):
    def __init__(self, targetName):
        self.myTargetName = targetName
    def __str__(self):
        return "No input stream for target '%s'" % self.myTargetName

class FailedToCreateIStreamByName(InvalidInputFiles):
    def __init__(self, className):
        self.myClassName = className
    def __str__(self):
        return "Failed to create class by name '%s'" % self.myClassName

class FileDoesntExist(InvalidInputFiles):
    def __init__(self, fileName):
        self.myFileName = fileName
    def __str__(self):
        return "File '%s' doesn't exist or is not a file" % self.myFileName

class FailedToOpenFile(InvalidInputFiles):
    def __init__(self, fileName, fileType):
        self.myFileName = fileName
        self.myFileType = fileType
    def __str__(self):
        return "Failed to open %s file '%s'" % (self.myFileType, self.myFileName)

class OutputException(Exception):
    pass

class UnknownOutputFileType(OutputException):
    def __init__(self, fileName):
        self.myFileName = fileName
    def __str__(self):
        return "Unsupported type of output file '%s'" % self.myFileName

class NoOutputStream(OutputException):
    def __init__(self, targetName):
        self.myTargetName = targetName
    def __str__(self):
        return "No output stream for target '%s'" % self.myTargetName

class InvalidOutputVariables(OutputException):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class CompilerSyntaxError(Exception):
    def __init__(self, offset):
        self.offset = offset
    def __str__(self):
        return "Syntax error at position %d" % self.offset

class ExecutorNotification(Exception):
    """This is not exception but rather a method to notify executor about some valid user input"""
    pass

class ExecutorSourceStatement(ExecutorNotification):
    """Notify executor to loasd another script"""
    def __init__(self, fileName):
        self.myFileName = fileName
    def getFileName(self):
        return self.myFileName
    def __str__(self):
        return "SOURCE %s" % self.myFileName

class UnexistingIStream:
    def __init__(self, inputType):
        self.myInputType = inputType
    def __str__(self):
        return "Input stream for type %s doesn't exist" % self.myInputType

class CompilationError(Exception):
    """General exception during compiling of miner commands into the python executable"""
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class MiningError(Exception):
    """General way of notifying executor about some error during mining"""
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class ReturnFromScript(Exception):
    def __str__(self):
        return "Returning from script"

## Functions
def class_isinstance(c, other):
    if c == other:
        return True
    for base in list(c.__bases__):
        if class_isinstance(base, other):
            return True
    return False

COMPLETE_NONE = 0
COMPLETE_STATEMENTS = 1
COMPLETE_COMMANDS = 2
COMPLETE_FOR_HELP = 3
COMPLETE_SYMBOLS = 4
COMPLETE_FILE = 5
COMPLETE_TOOLS = 6
COMPLETE_REPOSITORY = 7
COMPLETE_IMPORT = 8
COMPLETE_TARGET = 9

import types

class HelpClass(object):
    """This is base class for all miner commands and statements
    used for help and completer interface"""
    MORE_SYMBOLS_FOR_COMPLETION = []
    @staticmethod
    def getMoreSymbolsForCompletion(classType):
        try:
            val = classType.MORE_SYMBOLS_FOR_COMPLETION
        except:
            val = None
            for base in list(classType.__bases__):
                val = HelpClass.getMoreSymbolsForCompletion(base)
                if val:
                    break
            if not val:
                val = HelpClass.MORE_SYMBOLS_FOR_COMPLETION
        if isinstance(val, list):
            return val
        else:
            return val()

    @staticmethod
    def getLongHelp(classType):
        try:
            val = classType.LONG_HELP
        except:
            val = None
            for base in list(classType.__bases__):
                val = HelpClass.getLongHelp(base)
                if val:
                    break
            if not val:
                val = "No help available"
        if isinstance(val, types.FunctionType):
            return val()
        else:
            return val
    @staticmethod
    def getCompletionState(classType):
        try:
            return classType.COMPLETION_STATE
        except:
            for base in list(classType.__bases__):
                val = HelpClass.getCompletionState(base)
                if val:
                    return val
        return COMPLETE_NONE

