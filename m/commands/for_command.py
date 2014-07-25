#
# Copyright Michael Groys, 2012-2014
#

import miner_globals
from base import *

def p_for_command(p):
    '''command : for_command'''
    p[0] = p[1]

def p_for_select_command(p):
    '''for_command : FOR SELECT aggregated_named_expression_list'''
    p[0] = ForSelectCommand(p[3])

def p_for_dinstinct_select_command(p):
    '''for_command : FOR DISTINCT named_expression_list SELECT aggregated_named_expression_list'''
    p[0] = ForDistinctSelectCommand(p[3], p[5])

def p_for_dinstinct_select_ordered_command(p):
    '''for_command : FOR DISTINCT named_expression_list ascending SELECT aggregated_named_expression_list'''
    p[0] = ForDistinctSelectCommand(p[3], p[6], isOrdered=True, isAscending=p[4])

def p_for_in_select_command(p):
    '''for_command : FOR named_expression UC_IN expression SELECT aggregated_named_expression_list'''
    p[0] = ForInSelectCommand(p[2], p[4], p[6])

def p_for_each_of_select_command(p):
    '''for_command : FOR EACH expression OF named_expression SELECT aggregated_named_expression_list'''
    p[0] = ForEachOfSelectCommand(p[3], p[5], p[7])

def p_for_each_of_from_to_select_command(p):
    '''for_command : FOR EACH expression UC_IN expression ',' expression OF named_expression SELECT aggregated_named_expression_list'''
    p[0] = ForEachOfSelectCommand(p[3], p[9], p[11], p[5], p[7])

def p_for_each_of_from_select_command(p):
    '''for_command : FOR EACH expression UC_IN expression ',' OF named_expression SELECT aggregated_named_expression_list'''
    p[0] = ForEachOfSelectCommand(p[3], p[8], p[10], fromExpr=p[5])

def p_for_each_of_to_select_command(p):
    '''for_command : FOR EACH expression UC_IN ',' expression OF named_expression SELECT aggregated_named_expression_list'''
    p[0] = ForEachOfSelectCommand(p[3], p[8], p[10], toExpr=p[6])

def p_for_each_select_command(p):
    '''command : FOR EACH named_expression SELECT aggregated_named_expression_list'''
    p[0] = ForEachSelectCommand(p[3], p[5])

##############
# implementation classes
##############

class ForSelectCommand(TypicalCommand):
    NAME = "FOR SELECT"
    SHORT_HELP = "FOR SELECT <agg> exp1 [as name1], <agg> exp2 [as name2] ... - generates aggregated records"
    @staticmethod
    def LONG_HELP():
        s = """FOR SELECT <agg> exp1 [as name1], <agg> exp2 [as name2]
    FOR SELECT command performs aggregation query on the generated record set.
""" + ForSelectCommand.getAggregatorsHelp()
        return s
    @staticmethod
    def MORE_SYMBOLS_FOR_COMPLETION():
        return ["DISTINCT", "SELECT", "IN", "EACH", "OF"] + miner_globals.getAggregators()

    @staticmethod
    def getAggregatorsHelp():
        s = "Available aggregators are:\n"
        for agg in miner_globals.getAggregators():
            s += "    %-12s - %s\n" % (agg, miner_globals.getAggregatorHelp(agg))
        return s

    def __init__(self, aggregatedExpressions, aggregatedExpressionsOffset=0, preparationList=None):
        TypicalCommand.__init__(self, preparationList)
        self.myAggregatedExpressions = []
        i = aggregatedExpressionsOffset
        for (agg, exp, name, constructorArgs) in aggregatedExpressions:
            if not name:
                name = "_%d" % (i+1)
            self.myAggregatedExpressions.append( (agg, exp, name, constructorArgs) )
            i += 1

    def getVariableNames(self):
        return [e[2] for e in self.myAggregatedExpressions]

    def getAggregateDictionary(self):
        entries = []
        for aggregated in self.myAggregatedExpressions:
            constructorArgs = ""
            if aggregated[3]:
                constructorArgs = ", ".join(e.getValue() for e in aggregated[3])
            if aggregated[0].find('.') == -1:
                constructor = "%s(%s)" % (miner_globals.getAggregatorClass(aggregated[0]), constructorArgs)
            else:
                constructor = "%s(%s)" % (aggregated[0], constructorArgs)
            entries.append("'%s': %s" %(aggregated[2], constructor))
        return "{ %s }" %  ", ".join(entries)

    def getAddValuesSection(self, dictionaryName):
        s = ""
        for aggregated in self.myAggregatedExpressions:
            s += "        %s['%s'].add(%s)\n" % (dictionaryName, aggregated[2],
                                                 ", ".join(e.getValue() for e in aggregated[1]))
        return s
    def getDictionaryValues(self):
        return "".join(("_d['%s'].getValue(),"%aggregated[2]) for aggregated in self.myAggregatedExpressions)
    def getStart(self):
        s = TypicalCommand.getStart(self)
        return s+"    _d = %s\n" % self.getAggregateDictionary()
    def getBody(self):
        return self.getAddValuesSection("_d")
    def getEnd(self):
        return "    yield (%s)\n" % self.getDictionaryValues()
    def getGlobalExpressions(self):
        globalExps = TypicalCommand.getGlobalExpressions(self)
        for aggregated in self.myAggregatedExpressions:
            for e in aggregated[1]:
                globalExps.extend(e.getGlobalExpressions())
            if aggregated[3]:
                for e in aggregated[3]:
                    globalExps.extend(e.getGlobalExpressions())
        return globalExps
    def getStateForReduce(self):
        return "_d"
    def getReduceCommand(self, queueListStr, queueList):
        s = """
    _d = reduce(_runtime.mergeDictionaryItems, (q.get() for q in %s))
""" % (queueListStr, )
        return s

class ForDistinctSelectCommand(ForSelectCommand):
    NAME = "FOR DISTINCT"
    SHORT_HELP = "FOR DISTINCT expr1, ... [ASC|DESC] SELECT <agg> exp1 [as name1], ... - generates aggregated records for distinct sets"
    @staticmethod
    def LONG_HELP():
        s = """FOR DISTINCT expr1 [as name1], ... SELECT <agg> expN [as nameN], ...
FOR DISTINCT expr1 [as name1], ... (ASC|DESC) SELECT <agg> expN [as nameN], ...
    FOR DISTINCT command performs selective aggregation on the distinct set of records.
    If ASC or DESC is specified then results will be sorted accordingly, otherwise order of results is not defined
    For example count traffic generated to distinct hosts:
      FOR DISTINCT request.hosts SELECT sum response.length
""" + ForSelectCommand.getAggregatorsHelp()
        return s

    def __init__(self, distinctExpressions, aggregatedExpressions, isOrdered=False, isAscending=True, preparationList=None):
        ForSelectCommand.__init__(self, aggregatedExpressions, len(distinctExpressions), preparationList)
        self.myDistinctExpressions = distinctExpressions
        self.isOrdered = isOrdered
        self.isAscending = isAscending
        i = 0
        for exp in self.myDistinctExpressions:
            if not exp.getName():
                name = "_%d" % (i+1)
                exp.setName(name)
            i += 1
    def getVariableNames(self):
        return [e.getName() for e in self.myDistinctExpressions] + ForSelectCommand.getVariableNames(self)
    def getStart(self):
        s = ForSelectCommand.getStart(self)
        return s+"    _distincts = {}\n"
    def getDistinctTuple(self):
        tupleStr = createTupleString( [e.getValue() for e in self.myDistinctExpressions] )
        return tupleStr
    def getBody(self):
        s = """
        _t = %s
        if not _t in _distincts:
            _distincts[_t] = %s
        _d = _distincts[_t]
%s
""" % ( self.getDistinctTuple(), self.getAggregateDictionary(), self.getAddValuesSection("_d"))
        return s
    def getEnd(self):
        dictValues = self.getDictionaryValues()
        if self.isOrdered:
            reverseStr = "" if self.isAscending else ", reverse=True"
            itemsStr = "sorted(_distincts.items()%s)" % reverseStr
        else:
            itemsStr = "_distincts.iteritems()"
        return """
    for t, _d in %s:
        yield t + (%s)
""" % (itemsStr, dictValues)

    def getGlobalExpressions(self):
        globalExps = ForSelectCommand.getGlobalExpressions(self)
        for e in self.myDistinctExpressions:
            globalExps += e.getGlobalExpressions()
        return globalExps
    def getStateForReduce(self):
        return "_distincts"
    def getReduceCommand(self, queueListStr, queueList):
        s = """
    _distinctsList = [q.get() for q in %s]
    _distinctsMerged = _runtime.mergeDictionaryItemsToList(_distinctsList)
    _distincts = {}
    for key, dlist in _distinctsMerged.iteritems():
        d = reduce(_runtime.mergeDictionaryItems, dlist)
        _distincts[key] = d
""" % (queueListStr, )
        return s

class ForInSelectCommand(ForSelectCommand):
    NAME = "FOR IN"
    SHORT_HELP = "FOR expr [as name] IN sequenceExpr SELECT <agg> exp1 [as name1], ... - FOR IN - generates aggregated records for predefined sequence of values"
    @staticmethod
    def LONG_HELP():
        s = """FOR expr [as name] IN sequenceExpr SELECT <agg> exp1 [as name1], ...
    FOR IN command performs selective aggregation on the predefined sequence of values:
    For example to count requests to hosts youtube.com and xvideos.com:
      FOR request.host.split(".")[-2] as name in ["youtube", "xvideos"] SELECT count True as numRecords
""" + ForSelectCommand.getAggregatorsHelp()
        return s

    def __init__(self, forExpression, sequenceExpression, aggregatedExpressions):
        ForSelectCommand.__init__(self, aggregatedExpressions, 1)
        self.myForExpression = forExpression
        if not self.myForExpression.getName():
            self.myForExpression.setName("_1")
        self.mySequenceExpression = sequenceExpression
    def getVariableNames(self):
        return [self.myForExpression.getName()] + ForSelectCommand.getVariableNames(self)
    def getStart(self):
        s = ForSelectCommand.getStart(self)
        return s+"""    _distincts = {}
    _keys = [ k for k in %s ]
    for k in _keys:
        _distincts[k] = %s
""" % (self.mySequenceExpression.getValue(), self.getAggregateDictionary())
    def getBody(self):
        s = """
        _key = %s
        if not _key in _distincts:
            continue
        _d = _distincts[_key]
%s
""" % ( self.myForExpression.getValue(), self.getAddValuesSection("_d"))
        return s
    def getEnd(self):
        dictValues = self.getDictionaryValues()
        return """
    for key in %s:
        _d = _distincts[key]
        yield (key, %s)
""" % (self.mySequenceExpression.getValue(), dictValues)
    def getGlobalExpressions(self):
        return ForSelectCommand.getGlobalExpressions(self) + self.myForExpression.getGlobalExpressions()
    def getStateForReduce(self):
        return "_distincts"
    def getReduceCommand(self, queueListStr, queueList):
        s = """
    _distinctsList = [q.get() for q in %s]
    _distinctsMerged = _runtime.mergeDictionaryItemsToList(_distinctsList)
    _distincts = {}
    for key, dlist in _distinctsMerged.iteritems():
        d = reduce(_runtime.mergeDictionaryItems, dlist)
        _distincts[key] = d
""" % (queueListStr, )
        return s

class ForEachOfSelectCommand(ForSelectCommand):
    NAME = "FOR EACH"
    SHORT_HELP = "FOR EACH <bin-size> [IN <from>, <to>] OF <expr> [as <name] SELECT <agg> exp1 [as name1], ... - generates aggregated records for specified ranges"
    @staticmethod
    def LONG_HELP():
        s = """FOR EACH <bin-size> [IN <from>, <to>] OF <expr> [as <name] SELECT <agg> exp1 [as name1], ...
    FOR EACH command aggregates data in numeric ranges of specified by <bin-size>
    If <from> and <to> are not specified then from is defined by as min(exprMin, 0)
    and <to> is define by the expression maximum.
    For example: to count requests to sum volume at 1 hour time intervals run:
      FOR EACH 1h OF frecord.timeofday SELECT sum(frecord.downloadedContentBytes)
""" + ForSelectCommand.getAggregatorsHelp()
        return s

    def __init__(self, binSizeExpr, forExpression, aggregatedExpressions, fromExpr=None, toExpr=None):
        ForSelectCommand.__init__(self, aggregatedExpressions, 1)
        self.myForExpression = forExpression
        self.myBinSizeExpr = binSizeExpr
        self.myFromExpr = fromExpr
        self.myToExpr = toExpr
        if not self.myForExpression.getName():
            self.myForExpression.setName("_1")
    def getVariableNames(self):
        return [self.myForExpression.getName()] + ForSelectCommand.getVariableNames(self)
    def getStart(self):
        s = ForSelectCommand.getStart(self)
        s += """    _distincts = {}
    _step = %s
    _max = None
    _min = None
""" % self.myBinSizeExpr.getValue()
        if self.myFromExpr:
            s += "    _fromExpr = %s\n    _start = _fromExpr\n" % self.myFromExpr.getValue()
        else:
            s += "    _start = 0\n"
        if self.myToExpr:
            s += "    _toExpr = %s\n    _toExprKey = runtime.floor(_toExpr,_step, _start)\n" % self.myToExpr.getValue()
        return s
    def getBody(self):
        
        s = "        _key = runtime.floor(%s, _step, _start)\n" % self.myForExpression.getValue()
        if self.myFromExpr:
            s += """
        if _key < _fromExpr:
            continue
"""
        if self.myToExpr:
            s += """
        if _key > _toExprKey:
            continue
"""
        s += """
        if _key not in _distincts:
            _distincts[_key] = %s
        _d = _distincts[_key]
        if _min is None or _key < _min:
            _min = _key
        if _max is None or _key > _max:
            _max = _key
%s
""" % ( self.getAggregateDictionary(), self.getAddValuesSection("_d"))
        return s
    def getEnd(self):
        dictValues = self.getDictionaryValues()
        if self.myFromExpr:
            fromExprStr = "_from = _start"
        else:
            fromExprStr = "_from = runtime.floor(_min, _step, _start)"
        if self.myToExpr:
            toExprStr = "_to = runtime.floor(_toExpr, _step, _start)"
        else:
            toExprStr = "_to = runtime.floor(_max, _step, _start)"
        return """
    if _max is None:
        return
    %s
    %s
    _key = _from
    while True:
        _lookup = runtime.floor(_key,_step,_start)
        if _lookup not in _distincts:
            _d = %s
        else:
            _d = _distincts[_lookup]
        yield (_lookup, %s)
        if _key >= _to:
            break
        _key += _step
""" % (fromExprStr, toExprStr, self.getAggregateDictionary(), dictValues)
    def getGlobalExpressions(self):
        return ForSelectCommand.getGlobalExpressions(self) + self.myForExpression.getGlobalExpressions()
    def getStateForReduce(self):
        toExp = "_toExp" if self.myToExpr else "None"
        return "({'min':_min, 'max':_max, 'step':_step, 'start':_start, 'toExp' : %s}, _distincts)" % toExp
    def getReduceCommand(self, queueListStr, queueList):
        s = """
    _resultsList = [q.get() for q in %s]
    _min = min( [r[0]['min'] for r in _resultsList])
    _max = max( [r[0]['max'] for r in _resultsList])
    _step = _resultsList[0][0]['step']
    _toExp = _resultsList[0][0]['toExp']
""" % (queueListStr, )
        if self.myFromExpr:
            s += "    _start = _resultsList[0][0]['start']\n"
        else:
            s += "    _start = min( [r[0]['start'] for r in _resultsList])\n"

        s += """ 
    _distinctsMerged = _runtime.mergeDictionaryItemsToList( [t[1] for t in _resultsList] )
    _distincts = {}
    for key, dlist in _distinctsMerged.iteritems():
        d = reduce(_runtime.mergeDictionaryItems, dlist)
        _distincts[key] = d
"""
        return s

class ForEachSelectCommand(ForSelectCommand):
    NAME = "FOR EACH SELECT"
    SHORT_HELP = "FOR EACH <num> [as <name>] SELECT <agg> exp1 [as name1], ... - generates aggregated records for number of input records"
    @staticmethod
    def LONG_HELP():
        s = """FOR EACH <num> [as <name>] SELECT <agg> exp1 [as name1], ...
    Calculates aggergated expressions for number of input records:
      FOR EACH 1000 as recordId SELECT sum(volume)
""" + ForSelectCommand.getAggregatorsHelp()
        return s

    def __init__(self, numberInputsExp, aggregationExpressions, preparationList=None):
        ForSelectCommand.__init__(self, aggregationExpressions, 1, preparationList)
        self.numberInputsExp = numberInputsExp
        if not self.numberInputsExp.getName():
            self.numberInputsExp.setName("_1")
    def getVariableNames(self):
        return [self.numberInputsExp.getName()] + ForSelectCommand.getVariableNames(self)
    def getStart(self):
        s = ForSelectCommand.getStart(self)
        return s+"""
    _d = %s
    _id = 0
    _last = 0
    _mod = %s
""" % (self.getAggregateDictionary(), self.numberInputsExp.getValue())
    def getBody(self):
        s = """
        if _id - _last >= _mod:
            yield (_id,) + (%s)
            _last = _id
            _d = %s
        _id += 1
%s
""" % ( self.getDictionaryValues(), self.getAggregateDictionary(), self.getAddValuesSection("_d"))
        return s
    def getEnd(self):
        dictValues = self.getDictionaryValues()
        return """
    if _last != _id:
        yield (_id,) + (%s)
""" % dictValues

    def getGlobalExpressions(self):
        globalExps = ForSelectCommand.getGlobalExpressions(self)
        return globalExps + self.numberInputsExp.getGlobalExpressions()

miner_globals.addHelpClass(ForSelectCommand)
miner_globals.addHelpClass(ForDistinctSelectCommand)
miner_globals.addHelpClass(ForInSelectCommand)
miner_globals.addHelpClass(ForEachOfSelectCommand)
miner_globals.addHelpClass(ForEachSelectCommand)
miner_globals.addCommandName("FOR")

