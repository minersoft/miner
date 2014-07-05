import sys
import miner_globals
import m.common as common

def p_exit_statement(p):
    '''statement : EXIT'''
    ExitStatement.execute()

def p_exit_statement_with_code(p):
    '''statement : EXIT integer'''
    ExitStatement.execute(int(p[2]))

def p_return_statement(p):
    '''statement : RETURN'''
    p[0] = ReturnStatement()

def p_return_statement_expression(p):
    '''statement : RETURN expression'''
    p[0] = ReturnStatement(p[2])

class ExitStatement:
    NAME = "EXIT"
    SHORT_HELP = "EXIT [<status>] - exits miner"
    LONG_HELP = """EXIT [<status>]
    Exits miner,
    <status> specifies exit status code
"""
    @staticmethod
    def execute(status=0):
        sys.exit(status)

class ReturnStatement:
    NAME = "RETURN"
    SHORT_HELP = "RETURN [expression]- returns from miner or script"
    LONG_HELP = """RETURN
    Returns from miner or script
"""
    def __init__(self, expression=None):
        self.expression = expression

    def execute(self):
        import traceback
        if self.expression:
            try:
                res = miner_globals.evalExpression(self.expression.getValue())
                miner_globals.setReturnValue(str(res))
            except:
                traceback.print_exc()
                miner_globals.setReturnValue("-999")

        raise common.ReturnFromScript()

miner_globals.addHelpClass(ExitStatement)
miner_globals.addStatementName("EXIT")
miner_globals.addHelpClass(ReturnStatement)
miner_globals.addStatementName("RETURN")

