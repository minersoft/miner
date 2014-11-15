import miner_globals
from base import *

def p_source_merge_source(p):
    '''source : merge_source'''
    p[0] = p[1]

def p_merge_source_source(p):
    '''merge_source : MERGE BY expression '{' source '}' '''
    p[0] = MergeCommand(p[3])
    p[0].addChain(p[5], [])

def p_merge_source_chain(p):
    '''merge_source : MERGE BY expression '{' source  PIPE command_chain '}' '''
    p[0] = MergeCommand(p[3])
    p[0].addChain(p[5], p[7])

def p_merge_source_source_order(p):
    '''merge_source : MERGE BY expression ascending '{' source '}' '''
    p[0] = MergeCommand(p[3], isAscending=p[4])
    p[0].addChain(p[6], [])

def p_merge_source_chain_order(p):
    '''merge_source : MERGE BY expression ascending '{' source  PIPE command_chain '}' '''
    p[0] = MergeCommand(p[3], isAscending=p[4])
    p[0].addChain(p[6], p[8])

def p_merge_source_add_source(p):
    '''merge_source : merge_source '{' source '}' '''
    p[0] = p[1]
    p[0].addChain(p[3], [])

def p_merge_source_add_chain(p):
    '''merge_source : merge_source '{' source  PIPE command_chain '}' '''
    p[0] = p[1]
    p[0].addChain(p[3], p[5])

def p_merge_source_glue_source(p):
    '''merge_source : GLUE '{' source '}' '''
    p[0] = GlueCommand()
    p[0].addChain(p[3], [])

def p_merge_source_glue_chain(p):
    '''merge_source : GLUE '{' source  PIPE command_chain '}' '''
    p[0] = GlueCommand()
    p[0].addChain(p[3], p[5])



class MergeCommand(CommandBase):
    NAME = "MERGE"
    SHORT_HELP = "MERGE BY <expression> [ASC|DESC] { <mining-chain> } ... - merges data from multiple mining chains"
    LONG_HELP = """MERGE BY <expression> [ASC|DESC] { <mining-chain> } ...
    Merges data from multiple mining chains.
    Can be used for merging same type of data from multiple sources, e.g. frecords from line and delivery:
        MERGE BY frecord.timeofday {READ<frecord> *delivery*.arc} {READ<frecord> *video-analyzer*.arc} 
      or
        MERGE BY frecord.lastSeenNanosec {READ<frecord> *delivery*.arc|ACCUMULATE} {READ<frecord> *video-analyzer*.arc|ACCUMULATE}
    or different sources of data
        MERGE BY unixEndTime { READ<frecod> *.arc | |SELECT *, frecord.unixStartTime+(frecord.lastSeenNanosec-frecord.nanosec)as unixEndTime} \
                             { READ<transaction> *.qbl | SELECT *, msgData.myTimeOfDayGmtNanoseconds/1G as unixEndTime}
    In the later case variable set will be merged from both stacks with missed variables set to None.
"""
    def __init__(self, expression, isAscending=True):
        CommandBase.__init__(self)
        self.myExpression = expression
        self.isAscending = isAscending
        self.chains = []
        self.myVariables = None
        self.exportedGlobals = {}

    def getExportedGlobals(self, name):
        return self.exportedGlobals
    def addExportedGlobals(self, cmd, name):
        exportedGlobals = cmd.getExportedGlobals(name)
        if exportedGlobals:
            self.exportedGlobals.update(exportedGlobals)

    def addChain(self, source, chain):
        parent = source
        
        for command in chain:
            command.setParent(parent)
            parent = command
        
        variables = chain[-1].getVariableNames() if len(chain)>0 else source.getVariableNames()
        self.chains.append( (source, chain, variables) )
        
    def mergeVariables(self):
        mergedVariables = []
        for chain in self.chains:
            variables = chain[2]
            for v in variables:
                if v not in mergedVariables:
                    mergedVariables.append(v)
        return mergedVariables
        
    def getVariableNames(self):
        if not self.myVariables:
            self.myVariables = self.mergeVariables()
        return self.myVariables
    
    def createChainLoader(self, prefix, chain):
        parentName = "%s_loader" % prefix
        s = chain[0].createLoader(parentName)
        self.addExportedGlobals(chain[0], parentName)
        stack_id = 0
        for command in chain[1]:
            generatorName = "%s_stack%d" % (prefix, stack_id)
            s += command.createGenerator(generatorName, parentName)
            self.addExportedGlobals(command, generatorName)
            parentName = generatorName
            stack_id += 1
        # create variable adapter
        lastCommand = chain[1][-1] if len(chain[1])>0 else chain[0]
        s += self.createAdapter(prefix, lastCommand, parentName)
        parentName = prefix + "_adapter"
        return (s, parentName)
    
    def createAdapter(self, prefix, lastCommand, parentName):
        s = """
def %s_adapter():
    for %s in %s():
""" % (prefix, createTupleString(lastCommand.getVariableNames()), parentName)
        # fill missing variables with None
        for v in self.getVariableNames():
            if v not in lastCommand.getVariableNames():
                s += "        %s = None\n" % v
        s += "        _key = %s%s\n" % (("" if self.isAscending else "-"), self.myExpression.getValue())
        s += "        yield (_key, %s)\n" % createTupleString(self.getVariableNames())
        return s

    def createLoader(self, name):
        sources = []
        chain_id = 0
        s = ""
        for chain in self.chains:
            subStr, sourceName = self.createChainLoader("%s_merge%d"%(name, chain_id), chain)
            chain_id += 1
            sources.append(sourceName+"()")
            s += subStr
        s += """
def %s():
    import heapq
    for record in heapq.merge(%s):
        yield record[1]
""" % (name, ", ".join(sources))
        return s

class GlueCommand(MergeCommand):
    NAME = "GLUE"
    SHORT_HELP = "GLUE { <mining-chain> } ... - glues multiple sources to one"
    LONG_HELP = """GLUE { <mining-chain> } ...
    Glues multiple sources to one record by record stops when shortest source ends
    Common variables are overwritten
"""
    def __init__(self):
        MergeCommand.__init__(self, None)
    
    def createAdapter(self, prefix, lastCommand, parentName):
        s = """
def %s_adapter():
    for %s in %s():
        _e = {}
""" % (prefix, createTupleString(lastCommand.getVariableNames()), parentName)
        for v in lastCommand.getVariableNames():
            s += "        _e['%s'] = %s\n" % (v, v)
        s += "        yield _e\n"
        return s
    def createLoader(self, name):
        sources = []
        chain_id = 0
        s = ""
        for chain in self.chains:
            subStr, sourceName = self.createChainLoader("%s_glue%d"%(name, chain_id), chain)
            chain_id += 1
            sources.append(sourceName)
            s += subStr
    
        s += """
def %s():
""" % name
        for src in sources:
            s += "    _iter_%s = iter(%s())\n" % (src, src)
        s += """
    while True:
        _d = {}
"""
        for src in sources:
            s += "        _d.update(_iter_%s.next())\n" % src
        yieldValue = ",".join("_d['%s']"%v for v in self.getVariableNames())
        s += "        yield (%s)\n" % yieldValue 
        return s
    
miner_globals.addHelpClass(MergeCommand)
miner_globals.addHelpClass(GlueCommand)

miner_globals.addKeyWord(srcCommand="MERGE")
miner_globals.addKeyWord(srcCommand="GLUE")
miner_globals.addKeyWord(keyword="BY")
