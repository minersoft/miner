import miner_globals
import base
import m.common as common
from eval_statement import EvalStatement
from m.expressions import Expression
import re
import traceback

def p_statement_set(p):
    '''statement : set_statement
                | show_statement
                | show_all_statement
                | set_remove_statement'''
    p[0] = p[1]

def p_set_statement(p):
    '''set_statement : SET ID '=' expression '''
    p[4].setName(p[2])
    p[0] = Set(p[4])
    #Set.setValue(p[2], p[4])

def p_set_show_statement(p):
    '''show_statement : SET ID'''
    Set.show(p[2])

def p_set_show_all_statement(p):
    '''show_all_statement : SET'''
    Set.showAll()

def p_set_remove_statement(p):
    '''set_remove_statement : SET '-'  ID'''
    Set.remove(p[3])

def p_del_statement(p):
    '''statement : DEL expression '''
    p[0] = DelStatement(p[2])

SET_VAR_result = [None]

class Set(EvalStatement):
    NAME = "SET"
    SHORT_HELP = "SET [<name> [= <expression>]] - sets or dumps variables"
    LONG_HELP = """SET <name> = <expression>
SET <name>   - show value of variable
SET          - show values of all variables
SET - <name> - remove variable
    SET command is used to define value of global variable
    that can be used later in mining commands.
    The expression is evaluated once before command execution
"""
    COMPLETION_STATE = common.COMPLETE_SYMBOLS

    def __init__(self, expression):
        EvalStatement.__init__(self, expression)

    def getCommand(self):
        s = self.getImports()
        s += self.getGlobalVariables()
        if self.myExpression.getName() not in miner_globals.allVariables:
            miner_globals.allVariables[self.myExpression.getName()] = None
        s += "SET_VAR_result[0] = %s = %s\n" % (self.myExpression.getName(), self.myExpression.getValue())
        return s

    def getGlobalsDict(self, **mapping):
        global SET_VAR_result
        return EvalStatement.getGlobalsDict(self, SET_VAR_result=SET_VAR_result)

    def execute(self):
        global SET_VAR_result
        EvalStatement.execute(self)
        miner_globals.setVariable(self.myExpression.getName(), SET_VAR_result[0])
        self.getValue(self.myExpression.getName(), 50)

    @staticmethod
    def getValue(name, sizeLimit):
        import pprint
        if name not in miner_globals.allVariables:
            return "undefined"
        val = miner_globals.allVariables[name]
        if isinstance(val, dict) or isinstance(val, list):
            l = len(val)
            if l > sizeLimit:
                if isinstance(val, dict):
                    return "{ ... dictionary of size %d ...}" % l
                else:
                    return "{ ... list of size %d ...}" % l
        return pprint.pformat(val, depth=5)
    @staticmethod
    def showAll():
        for name, value in sorted(miner_globals.allVariables.iteritems()):
            print "%s = %s" % (name, Set.getValue(name, 50))
    @staticmethod
    def show(name):
        print Set.getValue(name, 500)
    @staticmethod
    def remove(name):
        miner_globals.removeVariable(name)

class DelStatement(base.StatementBase):
    NAME = "DEL"
    SHORT_HELP = "DEL <name>|<expression> - deletes variable or python object"
    LONG_HELP = """DEL <name> - deletes defined variable
DEL <expression> - deletes python expression
    DEL is used to delete defined variables or python objects: e.g. DEL myVar, DEL dict[1]
"""
    COMPLETION_STATE = common.COMPLETE_SYMBOLS
    def __init__(self, expression):
        self.expression = expression
    
    def execute(self):
        if re.match(r"^[_a-zA-Z][_a-zA-A0-9]*$", self.expression.getValue()):
            miner_globals.removeVariable(self.expression.getValue())
        else:
            try:
                miner_globals.execExpression("del " + self.expression.getValue())
            except NameError as e:
                print miner_globals.getExceptionLocation() + str(e)
            except (RuntimeError, TypeError) as e:
                print miner_globals.getExceptionLocation(),
                traceback.print_exc()
            except KeyError as e:
                print "%sUnexisting key: %s" % (miner_globals.getExceptionLocation(), str(e))

miner_globals.addHelpClass(Set)
miner_globals.addKeyWord(statement="SET")
miner_globals.addHelpClass(DelStatement)
miner_globals.addKeyWord(statement="DEL")

