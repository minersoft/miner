import miner_globals
import base
import re
import m.common as common
import traceback

def p_param_statement(p):
    '''statement : PARAM RAWSTRING'''
    nameValue = p[2]
    nameValue.lstrip()
    pos = nameValue.find('=')
    isConditional = False
    isExpression = False
    isAppend = False
    isRemove = False
    isSave = False
    if pos < 0:
        ParamStatement.printValue(p[2])
        return
    elif nameValue[0] == '-':
        isRemove = True
        name = nameValue[1:].lstrip()
    elif pos<=0:
        raise common.CompilerSyntaxError(p.lexpos(2))
    elif pos>1 and nameValue[pos-1]=='?':
        isConditional = True
        name = nameValue[:pos-1]
    elif pos>1 and nameValue[pos-1]==':':
        isExpression = True
        name = nameValue[:pos-1]
    elif pos>1 and nameValue[pos-1]=='+':
        isAppend = True
        name = nameValue[:pos-1]
    elif pos>1 and nameValue[pos-1]=='*':
        isSave = True
        name = nameValue[:pos-1]
    else:
        name = nameValue[:pos]
    name = name.rstrip()
    if not re.match("^[_a-zA-Z][_a-zA-Z0-9]*$", name):
        raise common.CompilerSyntaxError(p.lexpos(2))
    if isRemove:
        ParamStatement.removeValue(name)
        return
    value = nameValue[pos+1:]
    value = value.strip()
    if isAppend:
        ParamStatement.appendValue(name, value)
    elif isConditional:
        ParamStatement.setValueIfNotDefined(name, value)
    elif isExpression:
        ParamStatement.setValueExpression(name, value)
    elif isSave:
        ParamStatement.saveValue(name, value)
    else:
        ParamStatement.setValue(name, value)

def p_status_statement(p):
    '''statement : STATUS constant'''
    p[0] = StatusStatement(p[2])

class ParamStatement(base.StatementBase):
    NAME = "PARAM"
    SHORT_HELP = 'PARAM name=value'
    LONG_HELP = """PARAM name=value
PARAM -name
PARAM name?=value
PARAM name+=value
PARAM name*=value
PARAM name:= <python-expression>
    Sets global parameter value.
    PARAM -name   - removes <name> parameter
    If '?=' form is used then value is set only if it is not already defined
       ':=' allows to specify python expression on the right side
       '*=' updates and saves parameter as registry
"""
    COMPLETION_STATE = common.COMPLETE_FILE

    @staticmethod
    def appendValue(id, value):
        if id not in miner_globals.scriptParameters:
            miner_globals.setScriptParameter(id, value)
        else:
            miner_globals.setScriptParameter(id, miner_globals.getScriptParameter(id,"")+" "+value)
    @staticmethod
    def setValue(id, value):
        miner_globals.setScriptParameter(id, value)
    @staticmethod
    def removeValue(id):
        miner_globals.removeScriptParameter(id)
    @staticmethod
    def setValueIfNotDefined(id, value):
        if id not in miner_globals.scriptParameters:
            miner_globals.setScriptParameter(id, value)
    @staticmethod
    def setValueExpression(id,value):
        globalDict = dict(globals().items() + miner_globals.allVariables.items() + miner_globals.getImportedModules())
        try:
            res = eval(value, globalDict)
        except:
            traceback.print_exc()
            raise common.ReturnFromScript
        miner_globals.setScriptParameter(id, str(res))
    @staticmethod
    def saveValue(id, value):
        miner_globals.updateRegistry(id, value)
    @staticmethod
    def printValue(id):
        val = miner_globals.getScriptParameter(id, None)
        if not val:
            print "PARAM '%s' is not defined" % id
        else:
            print "PARAM %s=%s" % (id, val)
            

class StatusStatement(base.StatementBase):
    NAME = "STATUS"
    SHORT_HELP = 'STATUS <value> - set status $? variable to <value>'
    LONG_HELP = """STATUS <value>
    Sets status variable to <value>.
    Status variable can be accessed by $?
    It is set also by script RETURN statement and in case of script execution failures
"""
    def __init__(self, value):
        self.value = value
    def execute(self):
        miner_globals.setScriptParameter("?", self.value)

miner_globals.addHelpClass(ParamStatement)
miner_globals.addKeyWord(statement="PARAM")

miner_globals.addHelpClass(StatusStatement)
miner_globals.addKeyWord(statement="STATUS")
