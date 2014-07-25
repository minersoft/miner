#
# Copyright Michael Groys, 2012-2014
#

#
# This file contains io command
# First input file is read once before mining command execution to
# validate its existance, check its correctness and detemine record variables
# In general file format is determined from the extension:
#   .qbl - coals records
#   .csv - coma separated values with variables names in the first line
#   .pic - pickle serialization

import miner_globals
from m.common import *
import m.io_targets as io_targets
import os
import glob
import re
from base import *
import m.data_provider
import m._runtime

#####
# parse rules
########

def p_destination(p):
    '''destination : WRITE streamvar_list FILENAME'''
    p[0] = Destination(p[3], streamVars = p[2])
    # we are now in file state so pop back
    p.lexer.begin("INITIAL")

def p_typed_destination(p):
    '''destination : WRITE STREAMTYPE streamvar_list FILENAME'''
    p[0] = Destination(p[4], destinationType=p[2], streamVars=p[3])
    # we are now in file state so pop back
    p.lexer.begin("INITIAL")

def p_tee_destination(p):
    '''command : TEE streamvar_list FILENAME'''
    p[0] = TeeCommand(p[3], streamVars = p[2])
    # we are now in file state so pop back
    p.lexer.begin("INITIAL")

def p_typed_tee_destination(p):
    '''command : TEE STREAMTYPE streamvar_list FILENAME'''
    p[0] = TeeCommand(p[4], destinationType=p[2], streamVars=p[3])
    # we are now in file state so pop back
    p.lexer.begin("INITIAL")

def p_destination_stdout(p):
    '''destination : STDOUT streamvar_list stdout_redirect'''
    p[0] = StdoutDestination(p[3], p[2])

def p_stdout_redirect_empty(p):
    '''stdout_redirect : '''
    p[0] = "stdout"

def p_stdout_redirect(p):
    '''stdout_redirect : '>' FILENAME'''
    p[0] = p[2]

def p_destination_less(p):
    '''destination : LESS streamvar_list'''
    p[0] = LessDestination(p[2])

def p_source_file_source(p):
    '''source : file_source'''
    p[0] = p[1]
    
def p_read_source(p):
    '''file_source : READ streamvar_list filename_list'''
    p[0] = Source(p[3], streamVars=p[2])
    p.lexer.begin('INITIAL')

def p_typed_read_source(p):
    '''file_source : READ STREAMTYPE streamvar_list filename_list'''
    p[0] = Source(p[4], sourceType=p[2], streamVars=p[3])
    p.lexer.begin('INITIAL')

def p_repository_source(p):
    '''file_source : RREAD streamvar_list filename_list'''
    p[0] = RepositorySource(p[3], streamVars=p[2])
    p.lexer.begin('INITIAL')

def p_iterator_source(p):
    '''source : ITERATE id_list IN expression'''
    p[0] = IteratorStream(p[2], p[4].getValue())

def p_store_destination_command(p):
    '''destination : STORE expression IN import_name'''
    p[0] = StoreCommand(expression=p[2], containerName=p[4])

def p_store_in_dict_destination_command(p):
    '''destination : STORE expression ':' expression IN import_name'''
    p[0] = StoreCommand(key=p[2], expression=p[4], containerName=p[6])

def p_store_in_variables(p):
    '''destination : STORE explicitly_named_list'''
    p[0] = StoreVariablesCommand(p[2])

#####
# Command classes
#####
def _streamVarsParam(streamVars):
    if not streamVars or not len(streamVars):
        return ""
    values = ", ".join(("'%s': %s" % item) for item in streamVars.iteritems())
    return ", **{%s}" % values

class Source(CommandBase):
    NAME = "READ"
    SHORT_HELP = "READ ['<'target-type'>'] files - Reads data for mining command"

    @staticmethod
    def LONG_HELP():
        s = """READ ['<'target-type'>'] [<variable>=<value> ...] files
    Reads data for mining command (splitting it to records)
    Files can contain general glob patterns
    By default type of data is determined by file extension but it can be overwritten by <target-type>
    <variable>=<value> are specific variables defined for this target type
Available targets are:
"""
        inputTargets = set(miner_globals.getInputTargetList())
        targetHelpList = miner_globals.getTargetHelp()
        for t in targetHelpList:
            if t[0] in inputTargets:
                s += "    %-20s - %s\n" % (t[0]+"["+t[1]+"]",t[2].replace('\n','\n'+' '*27))
        return s

    COMPLETION_STATE = COMPLETE_FILE

    def __init__(self, fileNamePatterns, sourceType=None, streamVars=None):
        CommandBase.__init__(self)
        self.dataProvider = m.data_provider.DataProvider.createDataProvider(fileNamePatterns, sourceType, streamVars)
        
        inputClass = io_targets.getInputStreamClass(self.dataProvider.getStreamType())
        self.myVars = inputClass.STATIC_VARIABLE_NAMES
        if not self.myVars:
            openedFile = self.dataProvider.peekFirstHandle()
            source = io_targets.iStreamFactory(self.dataProvider.getStreamType(), openedFile[1], self.dataProvider.getMoreVars())
            self.myVars = source.getVariableNames()
            source.close()


    def getExportedGlobals(self, name):
        return {name + "_dataProvider": self.dataProvider}
    
    def getDataProvider(self):
        return self.dataProvider
    def setDataProvider(self, dataProvider):
        self.dataProvider = dataProvider
    
    def getVariableNames(self):
        return self.myVars

    def createLoader(self, loaderName):
        sourceName = io_targets.getInputStreamClassName(self.dataProvider.getStreamType())
        if not sourceName:
            raise NoInputStream(self.mySourceType)

        progressType = miner_globals.getScriptParameter("MINING_PROGRESS", None)
        if not progressType and m._runtime.isVerbose():
            progressType = "list"
        if progressType == "number":
            miningMessage = """
        if numFiles>1 and readFiles<=numFiles:
            print "-- Mining %d/%d (%d%%)...\\r" % (readFiles,numFiles, readFiles*100/numFiles),
        else:
            print "-- Mining %d...          \\r" % readFiles,
        sys.stdout.flush()
"""
        elif progressType == "name":
            miningMessage = """
        print "-- Mining %s ...\\r" % fileName,
        sys.stdout.flush()
"""
        elif progressType == "list":
            miningMessage = """        print "-- Mining %s ..." % fileName\n"""
        else:
            miningMessage = ""

        s = """
def %s():
    global readRecords
    global %s_dataProvider
    readFiles = 0
    numFiles = %s_dataProvider.size()
    for fileName,fileHandle in %s_dataProvider.iterateHandles():
        istream = %s(fileHandle%s)
        readFiles += 1
%s
        for record in istream:
            readRecords += 1
            yield record
        istream.close()
""" %   (loaderName, loaderName, loaderName, loaderName, sourceName, _streamVarsParam(self.dataProvider.getMoreVars()), miningMessage)
        return s

class RepositorySource(Source):
    NAME = "RREAD"
    SHORT_HELP = "RREAD <repository-path> - Reads data for mining command from repository"
    LONG_HELP = """RREAD <repository-path>
    Reads data from repository.
    Prefix in repository specifies data type
    Last part of the path specifies the time range in the following format
    20130101--20130108,20130110,20130112-16--2013010112-18
"""
    COMPLETION_STATE = COMPLETE_REPOSITORY
    
    def __init__(self, fileNamePatterns, streamVars):
        uriList = []
        for f in fileNamePatterns:
            uriList.append("repository://" + f)
        Source.__init__(self, uriList, sourceType=None, streamVars=streamVars)


class IteratorStream(CommandBase):
    NAME = "ITERATE"
    SHORT_HELP = "ITERATE <var>[,<var>..] in <iterable> - generates miner input from iterable expression"
    LONG_HELP = """ITERATE <var>[,<var>..] in <iterable-expression>
    This command allows to generate miner input from container in memory or general iterable expression, e.g.:
        ITERATE i in range(1000000)
        ITERATE key,value in mymodule.dictionary.iteritems()
"""
    def __init__(self, streamVars, expression):
        CommandBase.__init__(self)
        self.myVars = streamVars
        self.myExpressionStr = expression

    def getVariableNames(self):
        return self.myVars

    def createLoader(self, loaderName):
        if len(self.myVars)==1:
            vars = self.myVars[0]
            yieldVars = "(%s,)" % vars
        else:
            vars = "(%s)" % ",".join(self.myVars)
            yieldVars  = vars
        recordStr = []
        s = """
def %s():
    global readRecords
    if _runtime.isVerbose():
        print '''-- Mining %s ...'''
    for %s in %s:
        readRecords += 1
        yield %s
""" %   (loaderName, self.myExpressionStr, vars, self.myExpressionStr, yieldVars)
        return s

class Destination(CommandBase):
    NAME = "WRITE"
    SHORT_HELP = "WRITE ['<'target-type'>'] file - writes output of mining command"

    @staticmethod
    def getTargetHelp():
        s = ""
        outputTargets = set(miner_globals.getOutputTargetList())
        targetHelpList = miner_globals.getTargetHelp()
        for t in targetHelpList:
            if t[0] in outputTargets:
                s += "    %-20s - %s\n" % (t[0]+"["+t[1]+"]",t[2].replace('\n','\n'+' '*27))
        return s

    @staticmethod
    def LONG_HELP():
        s = """WRITE ['<'target-type'>'] [<variable>=<value> ...] file
    Writes output of mining command
    By default type of data is determined by file extension but it can be overwritten by <target-type>
    <variable>=<value> are specific variables defined for this target type
Available targets are:
""" + Destination.getTargetHelp()
        return s

    COMPLETION_STATE = COMPLETE_FILE

    def __init__(self, fileName, destinationType=None, streamVars=None):
        CommandBase.__init__(self)
        self.myStreamVars = streamVars
        if not destinationType:
            if fileName == "stdout":
                self.myDestinationType = io_targets.getTypeByExtension("stdout")
            else:
                ext = os.path.splitext(fileName)[1]
                self.myDestinationType = io_targets.getTypeByExtension(ext)
                if not self.myDestinationType:
                    raise UnknownOutputFileType(fileName)
        else:
            self.myDestinationType = destinationType
        self.myFileName   = os.path.expanduser(fileName)
    def getConstructor(self):
        oStreamClass = io_targets.getOutputStreamClassName(self.myDestinationType)
        varListStr = ", ".join(('"%s"'%e) for e in self.myParent.getVariableNames())
        return """%s(r"%s", [%s] %s)""" % (oStreamClass, self.myFileName, varListStr, _streamVarsParam(self.myStreamVars))
    
    def createSaver(self, saverName, generatorName):
        s = """
def %s():
    if _runtime.isVerbose():
        print "-- Destination %%s" %% r"%s"
    ostream = %s
    global writeRecords
    for record in %s():
        writeRecords += 1
        ostream.save(record)
    ostream.close()
""" %   (saverName, self.myFileName, self.getConstructor(), generatorName)
        return s

class TeeCommand(Destination):
    NAME = "TEE"
    SHORT_HELP = "TEE ['<'target-type'>'] file - writes output of mining command and continues processing"
    
    @staticmethod
    def LONG_HELP():
        s = """TEE ['<'target-type'>'] [<variable>=<value> ...] file
    Writes output of mining command to file and continues processing
    By default type of data is determined by file extension but it can be overwritten by <target-type>
    <variable>=<value> are specific variables defined for this target type
Available targets are:
""" + Destination.getTargetHelp()
        return s
    def __init__(self, fileName, destinationType=None, streamVars=None):
        Destination.__init__(self, fileName, destinationType, streamVars)
    def getVariableNames(self):
        return self.myParent.getVariableNames()
    def createGenerator(self, name, parentGeneratorName):
        s = """
def %s():
    if _runtime.isVerbose():
        print "-- Intermediate destination %%s" %% r"%s"
    ostream = %s
    global writeRecords
    for record in %s():
        ostream.save(record)
        yield record
    ostream.close()

""" % (name, self.myFileName, self.getConstructor(), parentGeneratorName)
        return s

class StdoutDestination(Destination):
    NAME = "STDOUT"
    SHORT_HELP = "STDOUT [<var>=format ...]- writes output of mining command to stdout"
    LONG_HELP = """STDOUT [<var>=format ...]
    Writes formatted output of mining command to stdout
    Default format is specified by the value of DEFAULT_STDOUT_FORMAT parameter
    Possible formatters are:
      a="*"       - default formating - makes human readable number representation 
      a=<function>- user provided function that will be used to convert values
      a=10  b=-10 - specifies field length no conversion will be done (negative means assign to the right)
      a=10.2      - specifies floating conversion format with field length and precision
      a="%"       - percentage format, multiply by 100 and add '%' symbol
      a="i"       - unmodified integer
      a="B"       - Represents using binary factors (TB/GB/MB/KB/B)
      a="b"       - Prints boolean values - True/False
      a="x"       - hexadecimal format of fixed size int32
      a="xx"      - hexadecimal format of int 64
      a="ip"      - ipv4 representation from - uint
      a="T"       - converts unix epoch time to 2011-12-11 09:00:21
      a="t"       - represents seconds as hh:mm:ss 
      a="s"       - s default convert to string left align
      a="<"       - s default convert to string left align
      a=">"       - s default convert to string right align
      a="Tm"      - converts float unix epoch time to 2011-12-11 09:00:21.555
      a="mt"      - converts milliseconds to hh:mm:ss.mmm
      a="hex"     - converts string to hex representation: ff:aa:00....
      _=...       - will change default format for variables 
"""
    def __init__(self, fileName, streamVars=None):
        Destination.__init__(self, fileName, destinationType="stdout", streamVars=streamVars)

class LessDestination(Destination):
    NAME = "LESS"
    SHORT_HELP = "LESS - writes output of mining command to less pager"
    LONG_HELP = """LESS [<var>=format ...]
    Writes user friendly formatted output of mining command (see STDOUT) to less pager
"""
    def __init__(self, streamVars=None):
        Destination.__init__(self, "less", destinationType="less", streamVars=streamVars)

class StoreCommand(CommandBase):
    NAME = "STORE"
    SHORT_HELP = "STORE <expression> in <container> - stores mining results in container"
    
    LONG_HELP = """STORE <expression> in <container>
STORE <expression> : <expression> in <container>
    Stores mining results in container which is cleared before run.
    First form assumes that container is list.
    Second form assumes that container is dictionary
"""
    COMPLETION_STATE = COMPLETE_SYMBOLS
    def __init__(self, expression, containerName, key=None):
        CommandBase.__init__(self)
        self.myExpression = expression
        self.containerName = containerName
        self.key = key
    def createSaver(self, saverName, generatorName):
        if ('.' not in self.containerName) and (self.containerName not in miner_globals.allVariables):
            if self.key:
                miner_globals.setVariable(self.containerName, {})
            else:
                miner_globals.setVariable(self.containerName, [])

        if self.key:
            clearCommand = "" # don't clear the dictionary "%s.clear()" % self.containerName
            insertCommand = "%s[%s] = %s" % (self.containerName, self.key, self.myExpression.getValue())
        else:
            clearCommand = "%s[:] = []" % self.containerName
            insertCommand = "%s.append(%s)" % (self.containerName, self.myExpression.getValue())
        s = """
def %s():
    if _runtime.isVerbose():
        print "-- Destination %s"
    global writeRecords
    %s
    for %s in %s():
        %s
        writeRecords += 1
""" %   (saverName, self.containerName, clearCommand, createTupleString(self.myParent.getVariableNames()), generatorName, insertCommand)
        return s

class StoreVariablesCommand(CommandBase):
    def __init__(self, namedExpressions):
        CommandBase.__init__(self)
        self.expressions = namedExpressions
    def getExportedGlobals(self, name):
        return {name+'_setVariable': miner_globals.setVariable}
    def createSaver(self, saverName, generatorName):
        variableNames = ", ".join(e.getName() for e in self.expressions)
        s = """
def %s():
    global %s_setVariable
    if _runtime.isVerbose():
        print "-- Destination %s"
    global writeRecords
    for %s in %s():
        writeRecords += 1
""" %   (saverName, saverName, variableNames, createTupleString(self.myParent.getVariableNames()), generatorName)
        for e in self.expressions:
            s += "        %s_setVariable('%s', %s)\n" % (saverName, e.getName(), e.getValue())
        return s

miner_globals.addHelpClass(Source)
miner_globals.addHelpClass(RepositorySource)
miner_globals.addHelpClass(IteratorStream)
miner_globals.addHelpClass(Destination)
miner_globals.addHelpClass(TeeCommand)
miner_globals.addHelpClass(StdoutDestination)
miner_globals.addHelpClass(LessDestination)
miner_globals.addHelpClass(StoreCommand)
miner_globals.addCommandName("READ")
miner_globals.addCommandName("RREAD")
miner_globals.addCommandName("ITERATE")
miner_globals.addCommandName("WRITE")
miner_globals.addCommandName("TEE")
miner_globals.addCommandName("STDOUT")
miner_globals.addCommandName("LESS")
miner_globals.addCommandName("STORE")

