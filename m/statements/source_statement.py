import miner_globals
import m.common as common
import base

def p_source_statement(p):
    '''statement : SOURCE FILENAME'''
    p.lexer.begin("INITIAL")
    p[0] = SourceStatement(p[2])

def p_once_statement(p):
    '''statement : ONCE relative_import_name'''
    p.lexer.begin("INITIAL")
    p[0] = OnceStatement(p[2])

def p_call_statement(p):
    '''statement : CALL relative_import_name '(' named_parameter_list ')' '''
    p[0] = CallStatement(p[2], p[4])

def p_call_statement_no_params(p):
    '''statement : CALL relative_import_name '(' ')' '''
    p[0] = CallStatement(p[2], [])

class SourceStatement(base.StatementBase):
    NAME = "SOURCE"
    SHORT_HELP = "SOURCE <filename> - executes miner script"
    LONG_HELP = """SOURCE <filename>
    Executes miner script specified by <filename> in current script environment.
    All parameters changes will be available
"""
    COMPLETION_STATE = common.COMPLETE_FILE
    def __init__(self, fileName):
        base.StatementBase.__init__(self)
        self.fileName = fileName
    def execute(self):
        miner_globals.callScript(self.fileName)

class OnceStatement(SourceStatement):
    NAME = "ONCE"
    SHORT_HELP = "ONCE <filename> - executes miner script only once"
    LONG_HELP = """ONCE <filename>
    Executes miner script specified by <filename> in current script environment.
    All parameters changes will be available
    The script is executed only once even if multiple statements available
"""
    COMPLETION_STATE = common.COMPLETE_FILE
    ALREADY_EXECUTED=set()
    def __init__(self, fileName):
        SourceStatement.__init__(self, fileName)
        
    def execute(self):
        if self.fileName not in OnceStatement.ALREADY_EXECUTED:
            OnceStatement.ALREADY_EXECUTED.add(self.fileName)
            SourceStatement.execute(self)

class CallStatement(base.StatementBase):
    NAME = "CALL"
    SHORT_HELP = "CALL <scriptId>(paramName=paramValue, ...) - executes miner script"
    LONG_HELP = """CALL <scriptId>(paramName=paramValue, ...)
    Executes miner script in its own context.
    If script overwrites some parameters it is not reflected in perent's script environment
      scriptId   - is script in the tools folder or in relative notation (e.g. myTool.myScript, .myScript)
      paramName  - is the name of parameter -> _1 , _2 ... - positional parameters
                                               _o = "output" maps to -o "output"  
      paramValue - is the python expression 
      
"""
    def __init__(self, scriptId, parametersList):
        base.StatementBase.__init__(self)
        self.scriptId = scriptId
        self.parametersList = parametersList
    
    def execute(self):
        parametersMap = {}
        for e in self.parametersList:
            name, value = e.getValue().split("=", 1)
            name = name.strip()
            if name == "_o":
                name = ">"
            elif name.startswith("_"):
                try:
                    val = int(name[1:])
                    name = name[1:]
                except:
                    pass
            parametersMap[name] = str(miner_globals.evalExpression(value))
        miner_globals.callScript(self.scriptId, inPrivateEnvironment=True, **parametersMap)
        
miner_globals.addHelpClass(SourceStatement)
miner_globals.addStatementName("SOURCE")

miner_globals.addHelpClass(OnceStatement)
miner_globals.addStatementName("ONCE")

miner_globals.addHelpClass(CallStatement)
miner_globals.addStatementName("CALL")
