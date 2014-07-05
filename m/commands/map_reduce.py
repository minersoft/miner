import miner_globals
from base import *
import io_command
from m.common import *
import for_command

def p_source_map_source(p):
    '''source : map_source'''
    p[0] = p[1]

def p_map_source_rread(p):
    '''map_source : MAP INTEGER file_source CURLY_OPEN command_chain '}' '''
    p[0] = MapReduce(p[2])
    p[0].initSourceCommand(p[3])
    p[0].initChain(p[5])


def p_map_source_rread_reduce(p):
    '''map_source : MAP INTEGER file_source CURLY_OPEN command_chain '}' reduce_command'''
    p[0] = MapReduce(p[2])
    p[0].initSourceCommand(p[3])
    p[0].initChain(p[5])
    p[0].initReduceCommand(p[7][0])
    p[0].initPushStateCommand(p[7][1])

def p_reduce_command_for_command(p):
    '''reduce_command : REDUCE for_command'''
    p[0] = (p[2],p[2])

def p_reduce_command_sortby_command(p):
    '''reduce_command : REDUCE sortby_command'''
    p[0] = (p[2],None)

class DataMapNotSupported(InvalidInputFiles):
    def __init__(self, dataProvider):
        self.dataProvider = dataProvider
    def __str__(self):
        return "Mapping is not supported by %s data provider" % self.dataProvider

class MapReduce(CommandBase):
    NAME = "REDUCE"
    SHORT_HELP = "MAP num RREAD/READ <files> { commands } REDUCE ... - performs map reduce command"
    LONG_HELP = """MAP num READ/RREAD <files> { commands } REDUCE ...
MAP num READ[<streamtype>] <files> { commands } REDUCE ...
    Performs mining of files by splitting it between <num> child processes.
    See help of MAP command for more information about file mapping
    Following REDUCE commands are supported
      REDUCE FOR SELECT ....
      REDUCE FOR DISTINCT .... SELECT ...
      REDUCE FOR EACH ... SELECT ...
      SORTBY ... ASC/DESC
"""
    COMPLETION_STATE = COMPLETE_SYMBOLS
    @staticmethod
    def MORE_SYMBOLS_FOR_COMPLETION():
        return for_command.ForSelectCommand.MORE_SYMBOLS_FOR_COMPLETION() + ["FOR", "SELECT", "DISTINCT", "SORTBY", "EACH"]

    def __init__(self, num):
        CommandBase.__init__(self)
        try:
            maxNumProcesses = int(miner_globals.getScriptParameter("MAPREDUCE_MAX_PROCESS_NUM", "10"))
        except:
            maxNumProcesses = 10
        if maxNumProcesses <= 0:
            raise CompilationError("MAP REDUCE command is not allowed")
        
        try:
            self.num = int(num)
             
            if self.num > maxNumProcesses:
                self.num = maxNumProcesses
        except:
            self.num = 1
        self.sourceCommand = None
        self.chain = None
        self.reduceCommand = None
        self.pushStateCommand = None
        self.exportedGlobals = {}
    def getExportedGlobals(self, name):
        return self.exportedGlobals
    def addExportedGlobals(self, cmd, name):
        exportedGlobals = cmd.getExportedGlobals(name)
        if exportedGlobals:
            self.exportedGlobals.update(exportedGlobals)
    def initSourceCommand(self, sourceCommand):
        self.sourceCommand = sourceCommand
        try:
            self.dataProviders = sourceCommand.getDataProvider().map(self.num)
            self.num = len(self.dataProviders)
        except:
            raise# DataMapNotSupported(sourceCommand.getDataProvider().getDataProviderName())
    def initChain(self, chain):
        self.chain = chain
        parent = self.sourceCommand
        for command in chain:
            command.setParent(parent)
            parent = command
    def initReduceCommand(self, reduceCommand):
        self.reduceCommand = reduceCommand
        if self.reduceCommand:
            self.reduceCommand.setParent(self.chain[-1])
    def initPushStateCommand(self, pushStateCommand):
        self.pushStateCommand = pushStateCommand
        if self.pushStateCommand:
            self.pushStateCommand.setParent(self.chain[-1])
    def getVariableNames(self):
        if self.reduceCommand:
            return self.reduceCommand.getVariableNames()
        else:
            return self.chain[-1].getVariableNames()

    def getReduce(self):
        if self.reduceCommand:
            queueList = ["q%d"%i for i in range(self.num)]
            queueListStr = "[" + ", ".join(queueList) + "]"
            s = self.reduceCommand.getReduceCommand(queueListStr, queueList)
            if self.pushStateCommand:
                s += self.reduceCommand.getEnd()
            return s
        # default
        s = ""
        for p in range(self.num):
            s += "    tryP%d = True\n" % p
        s += "    any = True\n"
        s += "    while any:\n"
        s += "        any = False"
        for p in range(self.num):
            s += """
        if tryP%d:
            for i in range(16):
                v = q%d.get()
                if v is None:
                    tryP%d = False
                    break
                else:
                    yield v
""" % (p, p, p)
        s += "        any = tryP0"
        for p in range(1, self.num):
            s += " or tryP%d" % p
        s += "\n"
        return s
    
    def createAdapter(self, loaderName, p, parentName):
        s = ""
        if not self.pushStateCommand and self.reduceCommand:
            lastGenerator = "%s_process%d_last"%(loaderName, p)
            s += self.reduceCommand.createGenerator(lastGenerator, parentName)
            self.addExportedGlobals(self.reduceCommand, lastGenerator)
            parentName = lastGenerator

        s += """def %s_process%d_adapter(q, readRecordsShared):\n""" % (loaderName, p)
        s += """  try:\n"""
        s += """    import time\n"""
        s += """    from Queue import Full\n"""
        s += """    global readRecords\n"""
        if self.pushStateCommand:
            s += """
%s
    for %s in %s():
%s
%s
""" % (self.reduceCommand.getStart(), createTupleString(self.reduceCommand.myParent.getVariableNames()), parentName, self.reduceCommand.getPreparationList(), self.reduceCommand.getBody())
            s += """    q.put(%s)\n""" % self.pushStateCommand.getStateForReduce()
        else:
            s += """
    maxFailedPuts = int(_runtime.getScriptParameter("MAP_REDUCE_PUT_TIMEOUT","30"))/0.1
    for r in %s():
        failedPuts = 0
        while failedPuts < maxFailedPuts:
            try:
                q.put_nowait(r)
                break
            except Full:
                time.sleep(0.1)
                failedPuts += 1
        if failedPuts == maxFailedPuts:
            # It is probably the case when LIMIT is used on main pipe
            # print "Queue is full exiting"
            os._exit(0)
    q.put(None)
    q.close()
""" % parentName
        s += """    readRecordsShared.value += readRecords
  except KeyboardInterrupt:
    os._exit(0)    
""" 
        return s
    
    def createChain(self, loaderName, p):
        import math
        s = ""
        parentName = "%s_process%d_loader" % (loaderName, p)
        self.sourceCommand.setDataProvider(self.dataProviders[p])
        s += self.sourceCommand.createLoader(parentName)
        self.addExportedGlobals(self.sourceCommand, parentName)
        
        stack_id = 0
        for command in self.chain:
            generatorName = "%s_process%d_stack%d" % (loaderName, p, stack_id)
            s += command.createGenerator(generatorName, parentName)
            self.addExportedGlobals(command, generatorName)
            parentName = generatorName
            stack_id += 1
        # create process adapter
        s += self.createAdapter(loaderName, p, parentName) 
        return s

    def createLoader(self, loaderName):
        s = """
def %s():
    from multiprocessing import Process, Queue, Value
    global readRecords
    readRecordsShared = Value('i', 0) 
""" % loaderName
        for p in range(self.num):
            s += """
    q%d = Queue(1024*1024) 
    p%d = Process(target=%s_process%d_adapter, args=(q%d, readRecordsShared))
    p%d.start()
""" % (p, p, loaderName, p, p, p)
        s += self.getReduce()
        for p in range(self.num):
            s += "    p%d.join()\n" % p
        s += "    readRecords = readRecordsShared.value\n"
        for p in range(self.num):
            s += self.createChain(loaderName, p)
        return s

class MapReduceHelpMap(CommandBase):
    NAME = "MAP"
    SHORT_HELP = "MAP num RREAD <files> { commands } [REDUCE ...] - performs map reduce command"
    LONG_HELP = """MAP num RREAD <files> { commands } [REDUCE ...]
MAP num READ[<streamtype>] <files> { commands } [REDUCE ...]
    Performs mining of files by splitting it between <num> child processes.
    For example if we haver 8 files and 3 processes they are split in the following way:
    (file1, file2, file3), (file4, file5, file6), (file7, file8)
    Maximum number of processes is 10.
    If REDUCE ... command is specified performs reduce by smart merging the result
    (e.g. global sorting or aggregation) otherwise just aggregates records. in the first coming order.
"""
    COMPLETION_STATE = COMPLETE_REPOSITORY

miner_globals.addHelpClass(MapReduce)
miner_globals.addHelpClass(MapReduceHelpMap)
miner_globals.addCommandName("MAP")
miner_globals.addCommandName("REDUCE")

