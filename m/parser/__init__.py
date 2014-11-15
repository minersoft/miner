#
# Copyright Michael Groys, 2012-2014
#

#
# This file implements main high level statements of miner language
#

import miner_globals
from exp_rules import *

# import definitions from all statement classes
from m.statements.alias import *
from m.statements.db_statement import *
from m.statements.doc_statement import *
from m.statements.exit_statement import *
from m.statements.eval_statement import *
from m.statements.help_statement import *
from m.statements.history import *
from m.statements.install_statement import *
from m.statements.import_statement import *
from m.statements.mining import *
from m.statements.param_statement import *
from m.statements.set_statement import *
from m.statements.shell_statement import *
from m.statements.source_statement import *
from m.statements.usage_statement import *
from m.statements.use_statement import *

from m.commands import *

import m.common as common
import miner_globals
import tokens as tokens_module
import m.keywords

for c in m.keywords.getAllKeyWords():
    tokens_module.reserved[c] = c

tokens_module.tokens.extend(list(tokens_module.reserved.values()))
tokens = tokens_module.tokens

# parsing rules
precedence = (
    ('right', 'LAMBDA'),
    ('right', '?', 'CONDITIONAL'),
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'UNARY_NOT'),
    ('left', '<', '>', 'LE', 'GE', 'EQ', 'NEQ', 'IN', 'IS'),
    ('nonassoc', 'MATCH_EQ', 'MATCH_NEQ' ),
    ('left', 'BINARY_OR'),
    ('left', '^'),
    ('left', '&'),
    ('left', '+', '-'),
    ('left', '*', '/', '%'),
    ('right', 'UNARY'),
    ('right', 'POW'),
    ('right', '@'),
    ('left', '.', '(', '[', 'POSTFIX')
)

#########
# Define parsing rules
#########

########################
# Sub rules
########################

# Import statement
def p_import_name(p):
    '''import_name : ID'''
    p[0] = p[1]

def p_import_name_ID(p):
    '''import_name : import_name '.' ID'''
    p[0] = p[1] + '.' + p[3]

def p_relative_import_name(p):
    '''relative_import_name : import_name'''
    p[0] = p[1]

def p_relative_import_name_dot(p):
    '''relative_import_name : '.' relative_import_name'''
    p[0] = '.' + p[1]

def p_ascending(p):
    '''ascending : ASC'''
    p[0] = True

def p_descending(p):
    '''ascending : DESC'''
    p[0] = False

# Filename list
# used in "source"
def p_filename_list(p):
    '''filename_list : FILENAME '''
    p[0] = [ p[1] ]

def p_filename_list_FILENAME(p):
    '''filename_list : filename_list FILENAME '''
    p[0] = p[1]
    p[0].append(p[2])

# Stream variables used in source and destination
def p_streamvar_list(p):
    '''streamvar_list : '''
    p[0] = {}

def p_streamvar_list_streamvar(p):
    '''streamvar_list : streamvar_list STREAMVAR'''
    p[0] = p[1]
    p[0][p[2][0]] = p[2][1]


# Error rule for syntax errors
def p_error(t):
    raise common.CompilerSyntaxError(t.lexpos if t else -1)


all_p_commands = filter(lambda var: var.startswith("p_"), dir())

__all__ = all_p_commands + ["statementNames"]

#print __all__

