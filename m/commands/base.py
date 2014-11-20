#
# Copyright Michael Groys, 2012-2014
#

#
# This file contains definition of different commands used in mining statement
# Each command is responsible to create code text for its generator function
#

from m.common import *

def createTupleString(listValues):
    if len(listValues) == 1:
        return "( %s, )" % listValues[0]
    else:
        return "( " + ", ".join(listValues) + " )"

def createNamedParameters(listValues):
    return ", ".join("%s = %s" % (e,e) for e in listValues)

class CommandBase(GeneratorBase, HelpClass):
    '''
    Base class for all commands
    '''
    def __init__(self):
        GeneratorBase.__init__(self)
    def createGenerator(self, name, parentGeneratorName):
        '''
        Main logic of a command
        It is responsible to generate code which performs command logic: yield records
          name - name of function to generate
          parentGeneratorName - name of parent generator function
          returns - string containing implementation of command logic
        '''
        raise NotImplementedError
    def createLoader(self, name):
        '''
        Should be implemented if command is loader like READ
        '''
        raise NotImplementedError
    def getExportedGlobals(self, name):
        '''
        Specifies list of global symbols that command wants to export to execution stack
        name can be used to scope such global symbols  
        '''
        return None
    def createSaver(self, name, parentGeneratorName):
        '''
        Implemented if command is saver like write
        '''
        raise NotImplementedError
    def getVariableNames(self):
        '''
        Returns record variables of the command
        '''
        raise NotImplementedError
    def getRequiredVars(self):
        '''
        Returns list of variables used in command for some minimal validation
        '''
        return []
    def getFinalizeCallback(self):
        '''
        May specify callback that will be executed after completion of miner operation
        '''
        return None
    # completion state describes state used for internal command completions
    COMPLETION_STATE = COMPLETE_SYMBOLS
    MORE_SYMBOLS_FOR_COMPLETION = []

class TypicalCommand(CommandBase):
    '''
    Typical command consists of main loop over parent generator
    with hook places for start section before loop, loop body and end section after loop
    '''
    def __init__(self, preparationList = None):
        '''
        preparationList - specifies list of expressions that should be evaluated before actual command execution
        '''
        CommandBase.__init__(self)
        self.myPreparationList = preparationList
    def createGenerator(self, name, parentGeneratorName):
        return """
def %s():
%s
    for %s in %s():
%s
%s
%s
""" %   (name, self.getStart(), createTupleString(self.myParent.getVariableNames()), parentGeneratorName, self.getPreparationList(), self.getBody(), self.getEnd())

    def getBody(self):
        '''Returns loop body - alignment 8 spaces'''
        raise NotImplementedError
    def getEnd(self):
        '''Returns section after loop - alignment 4 spaces'''
        return ""
    def getStart(self):
        '''Returns section before loop - alignment 4 spaces'''
        # create global explessions
        globalExps = self.getGlobalExpressions()
        s = ""
        for g in globalExps:
            s += g.getGlobalSection()
        return s
    def getGlobalExpressions(self):
        globalExps = []
        if self.myPreparationList:
            for exp in self.myPreparationList:
                globalExps.extend(exp.getGlobalExpressions() )
        return globalExps
    def getPreparationList(self):
        s = ""
        if self.myPreparationList:
            for exp in self.myPreparationList:
                s += """        %s""" % exp.getValue()
        return s

