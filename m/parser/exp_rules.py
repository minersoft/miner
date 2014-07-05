from m.expressions import *

#####################
# Expression rules
#####################
def p_expression(p):
    '''expression : ID'''
    p[0] = Expression()
    p[0].setId(p[1])

def p_expression_constant(p):
    '''expression : constant '''
    p[0] = Expression()
    p[0].setValue(p[1])

def p_integer(p):
    '''integer : INTEGER
                | HEXINTEGER
                | OCTINTEGER
                | BININTEGER'''
    p[0] = p[1]

def p_constant(p):
    '''constant : integer
                | FLOAT
                | STRING
                | TRUE
                | FALSE
                | NONE '''
    p[0] = p[1]
def p_expression_deref(p):
    '''expression : expression '.' ID'''
    p[0] = Expression()
    p[0].setDeref(p[1], p[3])

def p_expression_index(p):
    '''expression : expression '[' expression ']' %prec POSTFIX'''
    p[0] = Expression()
    p[0].setListAccess(p[1], p[3])

def p_expression_range_from_to(p):
    '''expression : expression '[' expression ':' expression ']' %prec POSTFIX'''
    p[0] = Expression()
    p[0].setListRange(p[1], p[3], p[5])

def p_expression_range_from(p):
    '''expression : expression '[' expression ':' ']' %prec POSTFIX'''
    p[0] = Expression()
    p[0].setListRange(p[1], p[3], None)

def p_expression_range_to(p):
    '''expression : expression '[' ':' expression ']' %prec POSTFIX'''
    p[0] = Expression()
    p[0].setListRange(p[1], None, p[4])

def p_expression_range_whole(p):
    '''expression : expression '[' ':' ']' %prec POSTFIX'''
    p[0] = Expression()
    p[0].setListRange(p[1], None, None)

def p_named_expression_list(p):
    '''named_expression_list : named_expression'''
    p[0] = [ p[1] ]

def p_named_expression_list_named_expression(p):
    '''named_expression_list : named_expression_list ',' named_expression'''
    p[0] = p[1]
    p[0].append(p[3])

def p_aggregated_named_expression_list(p):
    '''aggregated_named_expression_list : aggregated_named_expression'''
    p[0] = [ p[1] ]

def p_aggregated_named_expression_list_named_expression(p):
    '''aggregated_named_expression_list : aggregated_named_expression_list ',' aggregated_named_expression'''
    p[0] = p[1]
    p[0].append(p[3])

def p_aggregated_expression(p):
    '''aggregated_named_expression : import_name '(' not_empty_expression_list ')'
                                   | import_name '(' not_empty_expression_list ')' AS ID'''
    if len(p) == 7:
        name = p[6]
    elif len(p[3]) == 1:
        name = p[3][0].getName()
    else:
        name = ""
    p[0] = (p[1], p[3], name, None)

def p_aggregated_expression_constructor(p):
    '''aggregated_named_expression : import_name '(' not_empty_expression_list ')' '(' not_empty_expression_list ')'
                                   | import_name '(' not_empty_expression_list ')' '(' not_empty_expression_list ')' AS ID'''
    if len(p) == 10:
        name = p[9]
    elif len(p[6]) == 1:
        name = p[6][0].getName()
    else:
        name = ""
    p[0] = (p[1], p[6], name, p[3])

def p_named_expression(p):
    '''named_expression : expression'''
    p[0] = p[1]

def p_named_expression_as(p):
    '''named_expression : expression AS ID'''
    p[0] = p[1]
    p[0].setName(p[3])

def p_id_list(p):
    '''id_list : ID'''
    p[0] = [ p[1] ]

def p_id_list_id(p):
    '''id_list : id_list ',' ID'''
    p[0] = p[1]
    p[0].append(p[3])

def p_explicitly_named_as(p):
    '''explicitly_named : expression AS ID'''
    p[0] = p[1]
    p[0].setName(p[3])

def p_explicitly_named_id(p):
    '''explicitly_named : ID'''
    p[0] = Expression()
    p[0].setId(p[1])

def p_explicitly_named_list(p):
    '''explicitly_named_list : explicitly_named'''
    p[0] = [ p[1] ] 

def p_explicitly_named_list_append(p):
    '''explicitly_named_list : explicitly_named_list ',' explicitly_named'''
    p[0] = p[1]
    p[0].append(p[3]) 

#################
# Arithmetical expressions
#################
def p_exp_binary_exp(p):
    '''expression : expression '+' expression
                  | expression '-' expression
                  | expression '*' expression
                  | expression '/' expression
                  | expression '%' expression
                  | expression POW expression
                  | expression '<' expression
                  | expression '>' expression
                  | expression LE   expression
                  | expression GE   expression
                  | expression EQ   expression
                  | expression NEQ  expression
                  | expression OR   expression
                  | expression AND  expression
                  | expression IN   expression
                  | expression IS   expression
                  | expression '&'  expression
                  | expression '^'  expression
                  | expression SHIFT_LEFT  expression
                  | expression SHIFT_RIGHT expression
                  | expression FLOORDIV    expression'''
    p[0] = Expression()
    p[0].setBinary(p[1], p[2], p[3])

def p_assign_expression(p):
    '''assign_expression : expression '=' expression'''
    p[0] = Expression()
    p[0].setBinary(p[1], p[2], p[3])

def p_assign_arith_expression(p):
    '''assign_expression : expression '+' '=' expression
                         | expression '-' '=' expression
                         | expression '*' '=' expression
                         | expression '/' '=' expression
                         | expression '&' '=' expression
                         '''
    p[0] = Expression()
    p[0].setBinary(p[1], p[2]+"=", p[4])

def p_assign_expression_or_equal(p):
    '''assign_expression : expression OR_EQUAL expression'''
    p[0] = Expression()
    p[0].setBinary(p[1], p[2], p[3])
    

def p_exp_not_in_exp(p):
    '''expression : expression NOT IN expression %prec IN'''
    p[0] = Expression()
    p[0].setBinary(p[1], "not in", p[4])

def p_exp_is_not_exp(p):
    '''expression : expression IS NOT expression %prec IS'''
    p[0] = Expression()
    p[0].setBinary(p[1], "is not", p[4])

def p_expression_binary_or(p):
    '''expression : expression BINARY_OR expression '''
    p[0] = Expression()
    p[0].setBinary(p[1], '|', p[3])

def p_unary_exp(p):
    '''expression : '-' expression %prec UNARY
                  | '+' expression %prec UNARY
                  | '~' expression %prec UNARY
                  | NOT expression %prec UNARY_NOT'''
    p[0] = Expression()
    p[0].setUnary(p[1], p[2])

def p_expression_brackets(p):
    "expression : '(' expression ')'"
    p[0] = Expression()
    p[0].setBracketExpression(p[2])

def p_expression_match(p):
    "expression : expression MATCH_EQ expression"
    p[0] = MatchExpression(p[1], p[3])

def p_expression_nmatch(p):
    "expression : expression MATCH_NEQ expression"
    p[0] = MatchExpression(p[1], p[3], negate=True)

def p_function_call(p):
    "expression : expression '(' expression_list ')' %prec POSTFIX"
    p[0] = Expression()
    p[0].setFunctionCall(p[1], p[3], None)

def p_function_call_named_parameters(p):
    "expression : expression '(' named_parameter_list ')' %prec POSTFIX"
    p[0] = Expression()
    p[0].setFunctionCall(p[1], None, p[3])

def p_function_call_both_types_of_parameters(p):
    "expression : expression '(' not_empty_expression_list ',' named_parameter_list ')' %prec POSTFIX"
    p[0] = Expression()
    p[0].setFunctionCall(p[1], p[3], p[5])

def p_expression_list(p):
    "expression_list : "
    p[0] = []

def p_expression_list_not_empty_expression_list(p):
    "expression_list : not_empty_expression_list"
    p[0] = p[1]

def p_not_empty_expression_list(p):
    "not_empty_expression_list : expression"
    p[0] = [ p[1] ]

def p_not_empty_expression_list_expression(p):
    "not_empty_expression_list : not_empty_expression_list ',' expression"
    p[0] = p[1]
    p[0].append(p[3])

def p_named_parameter_list(p):
    '''named_parameter_list : ID '=' expression'''
    exp = Expression()
    exp.setAssignment(p[1], p[3])
    p[0] = [ exp ]

def p_named_parameter_list_named_parameter(p):
    '''named_parameter_list : named_parameter_list ',' ID '=' expression'''
    p[0] = p[1]
    newExp = Expression()
    newExp.setAssignment(p[3], p[5])
    p[0].append(newExp)

def p_list_expression(p):
    '''expression : '[' expression_list ']' '''
    p[0] = Expression()
    p[0].setList(p[2])

def p_conditional_expression(p):
    '''expression : expression '?' expression ':' expression %prec CONDITIONAL'''
    p[0] = Expression()
    p[0].setConditional(p[1], p[3], p[5])

# Tuples
def p_expression_tuple_with_coma(p):
    '''expression : '(' tuple_with_coma ')' '''
    p[0] = Expression()
    p[0].setTupleWithComa(p[2])

def p_expression_tuple_without_coma(p):
    '''expression : '(' tuple_without_coma ')' '''
    p[0] = Expression()
    p[0].setTupleWithoutComa(p[2])

def p_tuple_with_coma(p):
    '''tuple_with_coma : expression ',' '''
    p[0] = [p[1]]

def p_tuple_without_coma(p):
    '''tuple_without_coma : tuple_with_coma expression '''
    p[0] = p[1]
    p[0].append(p[2])

def p_tuple_with_coma_without(p):
    '''tuple_with_coma : tuple_without_coma ',' '''
    p[0] = p[1]

# Counter expressions
def p_expression_counter_expression(p):
    '''expression : counter_expression '''
    p[0] = p[1]

def p_counter_expression(p):
    '''counter_expression : '@' ID'''
    p[0] = CounterExpression(p[2])

def p_dict_counter_expression(p):
    '''counter_expression : '@' ID '[' expression ']' '''
    p[0] = DictCounterExpression(p[2], p[4])

def p_counter_expression_preIncr(p):
    '''counter_expression : INCR counter_expression '''
    p[0] = p[2]
    p[0].preIncr()

def p_counter_expression_postIncr(p):
    '''counter_expression : counter_expression INCR '''
    p[0] = p[1]
    p[0].postIncr()

def p_counter_expression_preDecr(p):
    '''counter_expression : DECR counter_expression '''
    p[0] = p[2]
    p[0].preDecr()

def p_counter_expression_postDecr(p):
    '''counter_expression : counter_expression DECR '''
    p[0] = p[1]
    p[0].postDecr()

def p_counter_expression_add(p):
    '''counter_expression : counter_expression '+' '=' expression'''
    p[0] = p[1]
    p[0].add(p[4])

def p_counter_expression_sub(p):
    '''counter_expression : counter_expression '-' '=' expression'''
    p[0] = p[1]
    p[0].sub(p[4])

def p_counter_expression_method(p):
    '''counter_expression : counter_expression '.' ID '(' expression_list ')' '''
    p[0] = p[1]
    p[0].method(p[3], p[5])

def p_list_comprehension(p):
    '''expression : expression LC_FOR ID IN expression'''
    p[0] = Expression()
    p[0].setListComprehension(p[1], p[3], p[5])

## Dictionary rules

def p_dictionary_expression(p):
    '''expression : dictionary_expression '''
    p[0] = p[1]

def p_dictionary_expression_empty(p):
    '''dictionary_expression : '{'  '}' '''
    
    p[0] = Expression()
    p[0].setDictionaryItems( [] )
    
def p_dictionary_expression_items(p):
    '''dictionary_expression : '{' dict_items '}'
                             | '{' dict_items ',' '}' '''
    
    p[0] = Expression()
    p[0].setDictionaryItems(p[2])

def p_dict_items(p):
    '''dict_items : expression ':' expression'''
    p[0] = [(p[1], p[3])]

def p_dict_items_item(p):
    '''dict_items : dict_items ',' expression ':' expression'''
    p[0] = p[1]
    p[0].append( (p[3], p[5]) )

# lamdba expression
def p_expression_lambda_expression(p):
    '''expression : lambda_expression'''
    p[0] = p[1]

def p_lambda_expression(p):
    '''lambda_expression : LAMBDA id_list ':' expression'''
    p[0] = Expression()
    p[0].setLambda(p[2], p[4])

