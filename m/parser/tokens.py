import miner_globals
import m.keywords

#####################
# Syntax token definitions
#####################

tokens = [
    'INTEGER', 'HEXINTEGER', 'OCTINTEGER', 'BININTEGER',
    'FLOAT',
    'STRING',
    'ID',
    'GE', 'LE', 'EQ', 'NEQ', 'POW',
    'MATCH_EQ', 'MATCH_NEQ',
    'INCR', 'DECR',
    'FILENAME', 'STREAMTYPE', 'STREAMVAR',
    'ALIAS_ID',
    'SHIFT_LEFT', 'SHIFT_RIGHT',
    'FLOORDIV', 'BINARY_OR',
    'OR_EQUAL',
    'RAWSTRING',
    'PIPE',
    'CURLY_OPEN',
    ]

states = (
    ('files', 'inclusive'),
    ('raw', 'inclusive'),
)

reserved = {
    'not'   : 'NOT',
    'or'    : 'OR',
    'and'   : 'AND',
    'in'    : 'IN',
    'is'    : 'IS',
    'True'  : 'TRUE',
    'False' : 'FALSE',
    'None'  : 'NONE',
    'as'    : 'AS',
    'for'   : 'LC_FOR',
    'IN'    : 'UC_IN',
    'lambda': 'LAMBDA', 
    'WITH'  : 'WITH',
    }

literals = [',', '.', '+', '-', '*', '%', '/', '=', '<', '>', '?', '(', ')', '[', ']', ':', '&', '^', '@', ';', '{', '}']

t_raw_RAWSTRING = r'.+'
#t_STRING = r'\"([^\\"]|(\\.))*\"'
t_HEXINTEGER = r'0[xX][0-9a-fA-F]+[lL]?'
t_OCTINTEGER = r'0[oO]?[0-7]+[lL]?'
t_BININTEGER = r'0[bB][0-1]+[lL]?'
t_GE  = r'>='
t_LE  = r'<='
t_EQ  = r'=='
t_NEQ = r'!='
t_MATCH_EQ  = r'=~'
t_MATCH_NEQ = r'!~'
t_POW  = r'\*\*'
t_INCR = r'\+\+'
t_DECR = r'--'
t_SHIFT_LEFT  = r'\<\<'
t_SHIFT_RIGHT = r'\>\>'
t_FLOORDIV    = r'//'
t_BINARY_OR   = r'\|\|'
t_OR_EQUAL    = r'\|='
t_PIPE = r'\|'

t_ignore  = ' \t'
t_files_ignore  = ' \t'

tpart_exponent      =  r"[eE][-+]?\d+"
tpart_pointfloat    =  r"((\d+)?\.\d+)|(\d+\.)"

tpart_int_exponent =  r"\d+%s" % tpart_exponent
tpart_float_opt_exponent =  r"(%s)(%s)?" % (tpart_pointfloat, tpart_exponent)

####t_FLOAT = "%s|%s" % (tpart_pointfloat, tpart_exponentfloat)

t_FLOAT =  "%s|%s" % (tpart_int_exponent, tpart_float_opt_exponent)

t_INTEGER    = r'[1-9]\d*[lL]?|0'

_bytesFactor  = {"T": 1024 * 1024 * 1024 * 1024,
                 "G": 1024 * 1024 * 1024,
                 "M": 1024 * 1024,
                 "K": 1024}
_numberFactor = {"T": 1000 * 1000 * 1000 * 1000,
                 "G": 1000 * 1000 * 1000,
                 "M": 1000 * 1000,
                 "K": 1000,
                 "d": 24 * 3600,
                 "h": 3600,
                 "m": 60}

def t_NUMBERBYTES(t):
    r"\d+[TGMK]B"
    number = int(t.value[:-2])
    suffix = t.value[-2]
    t.value = str(number*_bytesFactor[suffix])
    t.type = "INTEGER"
    return t

def t_FLOATBYTES(t):
    r"\d+\.(\d+)?[TGMK]B"
    number = float(t.value[:-2])
    suffix = t.value[-2]
    t.value = str(int(number*_bytesFactor[suffix]))
    t.type = "INTEGER"
    return t

def t_NUMBERSUFFIX(t):
    r"\d+(T|G|M|K|d|h|m)"
    number = int(t.value[:-1])
    suffix = t.value[-1]
    t.value = str(number*_numberFactor[suffix])
    t.type = "INTEGER"
    return t

def t_FLOATSUFFIX(t):
    r"\d+\.(\d+)?(T|G|M|K|d|h|m)"
    number = float(t.value[:-1])
    suffix = t.value[-1]
    t.value = str(number*_numberFactor[suffix])
    t.type = "FLOAT"
    return t

def t_TIME(t):
    r"\d\d\d\d(\d\d)?H"
    hours = int(t.value[0:2])
    minutes = int(t.value[2:4])
    if len(t.value)> 5:
        secs = int(t.value[4:6])
    else:
        secs = 0
    t.value = str(hours*3600+minutes*60+secs)
    t.type = "INTEGER"
    return t

def t_DATE(t):
    r"\d{8}D"
    from calendar import timegm
    year = int(t.value[0:4])
    month = int(t.value[4:6])
    day = int(t.value[6:8])
    val = timegm( (year, month, day, 0, 0, 0, 0, 0, 0) )
    t.value = str( val )
    t.type = "INTEGER"
    return t
    
files_literals = ['|', '{']

def t_files_STREAMTYPE(t):
    r'\<[-a-zA-Z0-9_]+\>'
    t.value = t.value[1:-1]
    return t

def t_files_PIPE(t):
    r'\|'
    t.lexer.begin('INITIAL')
    t.type = "PIPE"
    t.value = "|"
    return t

def t_files_CURLY_OPEN(t):
    r'\{'
    t.lexer.begin('INITIAL')
    t.type = "CURLY_OPEN"
    t.value = "{"
    return t
    
def t_files_STREAMVAR(t):
    r"""[_a-zA-Z]\w*=([^ \t"']+|"([^\\"]|(\\.))*"|'([^\\']|(\\.))*')"""
    equal = t.value.index('=')
    t.value = (t.value[:equal], t.value[equal+1:])
    return t

# This token is used to specify URIs, filenames or filename patterns
# it is active only in the <files> state (after READ and WRITE)
def t_files_FILENAME(t):
    r'([a-z]+:[^ \t\n\"\|\<\>]+)|([^ \t\n\"\|\<\>=}]+)|"[^"]*"'
    if t.value.startswith('"'):
        t.value = t.value[1:-1]
    return t

def t_longSingleSTRING(t):
    r"'''.*'''"
    t.type = 'STRING'
    return t

def t_longDoubleSTRING(t):
    r'""".*"""'
    t.type = 'STRING'
    return t

def t_rSTRING(t):
    r"""[ur]?\"([^\\"]|(\\.))*\"|[ur]?'([^\\']|(\\.))*'"""
    t.type = 'STRING'
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    if m.keywords.shouldSwitchToFileMode(t.type):
        # we need to switch to the special lexing state which tokenizes input as files
        t.lexer.begin('files')
    elif t.type == 'PARAM':
        t.lexer.begin('raw')
    elif t.value in miner_globals.aliasCommands:
        t.type = 'ALIAS_ID'

    return t

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

def t_files_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)


