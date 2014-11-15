import miner_globals
import m.common as common
import base
import traceback
import sys
import m.loggers as loggers

def p_eval_statement(p):
    '''statement : EVAL expression'''
    p[0] = EvalStatement(p[2], withReturn=False)

def p_eval_assign_statement(p):
    '''statement : EVAL assign_expression'''
    p[0] = EvalStatement(p[2], withReturn=False)

def p_print_statement(p):
    '''statement : PRINT expression_list'''
    p[0] = PrintStatement(p[2])

def p_print_statement_redirect(p):
    '''statement : PRINT SHIFT_RIGHT not_empty_expression_list'''
    p[0] = PrintStatement(p[3], redirect=True)

class EvalStatement(base.StatementBase):
    """
    Evaluate expression
    """
    NAME = "EVAL"
    SHORT_HELP = "EVAL <expression> - evaluates expression"
    LONG_HELP = """EVAL <expression>
    Evaluates expression
"""
    COMPLETION_STATE = common.COMPLETE_SYMBOLS

    def __init__(self, expression=None, withReturn=True):
        base.StatementBase.__init__(self)
        self.myExpression = expression
        self.withReturn = withReturn
    def getImports(self):
        """
        Gets import section
        """
        s = ""
        for i, val in miner_globals.importMap.iteritems():
            if val[0]:
                s += "import %s as %s\n" % (val[0], i)
            else:
                s += "import %s\n" % i
        return s

    def getGlobalVariables(self):
        """
        Gets global variables section
        """
        s = ""
        #for (name, val) in miner_globals.allVariables:
        #    s += "%s = %s\n" % (name, val)
        return s

    def getCommand(self):
        s = self.getImports()
        s += self.getGlobalVariables()
        s += "def evaluate():\n"
        for v in miner_globals.allVariables.keys():
            s += "    global %s\n" % v
        globalExpressions = self.myExpression.getGlobalExpressions()
        for e in globalExpressions:
            s += e.getGlobalSection()
        if self.withReturn:
            s += "    return "
        else:
            s += "    "
        s += self.myExpression.getValue() + "\n"
        if self.withReturn:
            s += "print "
        s += "evaluate()\n"
        return s

    def dump(self, handle=None):
        """Dumps command to stdout"""
        if handle == None:
            handle = sys.stdout
        s = self.getCommand()
        lines = s.split("\n")
        s = ""
        for i, line in enumerate(lines):
            s += "%3d: " % (i+1)
            s += line
            s += "\n"
        print >>handle, s
    
    def dumplog(self, log, context=""):
        if loggers.isEnabled(log):
            log.info("%s\n%s", context, self.getCommand())


    def getGlobalsDict(self, **mapping):
        return dict(globals().items() + miner_globals.allVariables.items(), **mapping)

    def execute(self):
        """
        Evaluates expression
        """
        s = self.getCommand()
        globalsDict = self.getGlobalsDict()
        try:
            exec s in globalsDict
        #except NameError as e:
        #    print miner_globals.getExceptionLocation()+str(e)
        except (RuntimeError, TypeError) as e:
            print miner_globals.getExceptionLocation(),
            traceback.print_exc()
            
            

class PrintStatement(EvalStatement):
    """
    Prints expression
    """
    NAME = "PRINT"
    SHORT_HELP = "PRINT <expression>[, ...] - evaluates expression"
    LONG_HELP = """PRINT <expression>[, ...]
    Prints expression list
"""
    def __init__(self, expressionList, redirect=False):
        EvalStatement.__init__(self)
        self.myExpressionList = expressionList
        self.redirect=redirect
    def getCommand(self):
        redirectStr = ">>" if self.redirect else ""
        s = self.getImports()
        s += self.getGlobalVariables()
        s += "def evaluate():\n"
        globalExpressions = []
        for e in self.myExpressionList:
            globalExpressions += e.getGlobalExpressions()
        for e in globalExpressions:
            s += e.getGlobalSection()
        s += "    print %s%s\n" % (redirectStr, ", ".join(e.getValue() for e in self.myExpressionList))
        s += "evaluate()\n"
        return s
    def execute(self):
        """
        Prints expression
        """
        s = self.getCommand()
        globalsDict = self.getGlobalsDict()
        try:
            exec s in globalsDict
        except (RuntimeError, TypeError, NameError) as e:
            print miner_globals.getExceptionLocation()+str(e)

miner_globals.addHelpClass(EvalStatement)
miner_globals.addKeyWord(statement="EVAL")
miner_globals.addHelpClass(PrintStatement)
miner_globals.addKeyWord(statement="PRINT")


