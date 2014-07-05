import miner_globals
import base

def p_history_statement(p):
    '''statement : HISTORY'''
    History.execute()

def p_history_statement_limit(p):
    '''statement : HISTORY integer'''
    History.execute(int(p[2]))

class History(base.StatementBase):
    NAME = "HISTORY"
    SHORT_HELP = "HISTORY [<num>] - dumps command history"
    LONG_HELP = """HISTORY [<num>]
    Dumps commans history,
    <num> specifies number of latest commands to dump - by default 10
          if <num> == 0 dumps all available history:
"""
    @staticmethod
    def execute(limit=10):
        import readline
        if limit <= 0:
            limit = 1000 # Some big number
        if readline.get_current_history_length() < limit:
            limit = readline.get_current_history_length()
        for index in range(readline.get_current_history_length()-limit, readline.get_current_history_length()):
            s = readline.get_history_item(index+1)
            print " %d: %s" % (index+1, s)

miner_globals.addHelpClass(History)
miner_globals.addStatementName("HISTORY")

