import time

import miner_globals
import m.common as common
import m.commands as commands
import m._runtime as _runtime

from eval_statement import EvalStatement

#####################
# Parse commands
#####################

def p_mining_statement(p):
    '''statement : source PIPE command_chain PIPE destination'''
    p[0] = MiningCommand(p[1], p[3], p[5])

def p_mining_statement_empty(p):
    '''statement : source PIPE destination'''
    p[0] = MiningCommand(p[1], [], p[3])

def p_command_chain_command(p):
    '''command_chain : command'''
    if isinstance(p[1], list):
        p[0] = list(p[1])
    else:
        p[0] = [p[1]]

def p_command_chain_add_command(p):
    '''command_chain : command_chain PIPE command'''
    p[0] = p[1]
    if isinstance(p[3], list):
        p[0].extend(p[3])
    else:
        p[0].append(p[3])


# Mining command definitions

def p_alias_command(p):
    '''command : ALIAS_ID'''
    commandList = miner_globals.aliasCommands.get(p[1], None)
    p[0] = commandList

#
# Other commands specified in m.commands and directly imported in m.parser
#

class MiningCommand(EvalStatement):
    """
    Generates and executes mining code
    """
    def __init__(self, source, stack, destination):
        """
        source      - io_command.Source
        stack       - list of Commands
        destination - io_command.Destintion
        """
        EvalStatement.__init__(self)
        self.mySource = source
        self.myDestination = destination
        self.stack = stack
        self.exportedGlobals = {}
        pos = 0
        for command in self.stack:
            if pos == 0:
                command.setParent(self.mySource)
            else:
                command.setParent(self.stack[pos-1])
            pos += 1
        if pos == 0:
            self.myDestination.setParent(self.mySource)
        else:
            self.myDestination.setParent(self.stack[pos-1])
    
    def addExportedGlobals(self, cmd, name):
        exportedGlobals = cmd.getExportedGlobals(name)
        if exportedGlobals:
            self.exportedGlobals.update(exportedGlobals)

    def getCommand(self):
        """
        Get whole command
        """
        s = self.getImports()
        s += self.getGlobalVariables()
        depth = 0
        s += self.mySource.createLoader("loader")
        self.addExportedGlobals(self.mySource, "loader")

        parentGenerator = self.mySource 
        generatorName = "loader"
        for command in self.stack:
            name = "stack%d"%depth
            s += command.createGenerator(name, generatorName)
            self.addExportedGlobals(command, name)
            generatorName = name
            parentGenerator = command
            depth += 1
        s += self.myDestination.createSaver("saver", generatorName)
        self.addExportedGlobals(self.myDestination, "saver")
        return s

    def execute(self):
        """
        Executes command
        Returns tuple consisting of (number of read records, number of written records, processing time in seconds)
        """
        readRecords = 0
        writeRecords = 0
        s = self.getCommand()
        s += "saver()\n"
        startTime = time.time()
        globalsDict = self.getGlobalsDict(readRecords=0, writeRecords=0, **self.exportedGlobals)
        #print "globalsDict", globalsDict 
        exec s in globalsDict
        readRecords = globalsDict['readRecords']
        writeRecords = globalsDict['writeRecords']
        endTime = time.time()
        miner_globals.setScriptParameter("coals", readRecords)
        miner_globals.setScriptParameter("diamonds", writeRecords)
        deltaTime = endTime-startTime
        if _runtime.isVerbose() or miner_globals.getScriptParameter("MINING_TIMING", None):
            if deltaTime<0.001:
                rate=0
            else:
                rate=readRecords/deltaTime
            print "Processed %d coals into %d diamonds for %.3f seconds, %d coals/sec." % (readRecords, writeRecords, deltaTime, rate)
        return

