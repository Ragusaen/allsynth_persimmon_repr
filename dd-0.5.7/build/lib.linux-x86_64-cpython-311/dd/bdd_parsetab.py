
# bdd_parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'exprleftCOLONleftEQUIVleftIMPLIESleftMINUSleftXORleftORleftANDleftEQUALSrightNOTrightUMINUSLPAREN RPAREN COMMA NOT AND OR XOR IMPLIES EQUIV EQUALS MINUS DIV AT COLON FORALL EXISTS RENAME NAME NUMBER TRUE FALSE ITEexpr : TRUE\n                | FALSE\n        expr : AT numbernumber : NUMBERnumber : MINUS NUMBER %prec UMINUSexpr : nameexpr : NOT exprexpr : expr AND expr\n                | expr OR expr\n                | expr XOR expr\n                | expr IMPLIES expr\n                | expr EQUIV expr\n                | expr EQUALS expr\n                | expr MINUS expr\n        expr : ITE LPAREN expr COMMA expr COMMA expr RPARENexpr : EXISTS names COLON expr\n                | FORALL names COLON expr\n        expr : RENAME subs COLON exprsubs : subs COMMA subsubs : subsub : name DIV namenames : names COMMA namenames : namename : NAMEexpr : LPAREN expr RPAREN'
    
_lr_action_items = {'TRUE':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,]),'FALSE':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,]),'AT':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,]),'NOT':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,]),'ITE':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,]),'EXISTS':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,]),'FORALL':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,]),'RENAME':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,]),'LPAREN':([0,6,7,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[8,8,24,8,8,8,8,8,8,8,8,8,8,8,8,8,8,]),'NAME':([0,6,8,9,10,11,13,14,15,16,17,18,19,24,42,43,44,45,46,47,48,56,],[12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,]),'$end':([1,2,3,5,12,20,21,23,32,33,34,35,36,37,38,39,41,49,51,52,58,],[0,-1,-2,-6,-24,-3,-4,-7,-8,-9,-10,-11,-12,-13,-14,-5,-25,-16,-17,-18,-15,]),'AND':([1,2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[13,-1,-2,-6,-24,-3,-4,-7,13,-8,13,13,13,13,-13,13,-5,13,-25,13,13,13,13,13,-15,]),'OR':([1,2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[14,-1,-2,-6,-24,-3,-4,-7,14,-8,-9,14,14,14,-13,14,-5,14,-25,14,14,14,14,14,-15,]),'XOR':([1,2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[15,-1,-2,-6,-24,-3,-4,-7,15,-8,-9,-10,15,15,-13,15,-5,15,-25,15,15,15,15,15,-15,]),'IMPLIES':([1,2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[16,-1,-2,-6,-24,-3,-4,-7,16,-8,-9,-10,-11,16,-13,-14,-5,16,-25,16,16,16,16,16,-15,]),'EQUIV':([1,2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[17,-1,-2,-6,-24,-3,-4,-7,17,-8,-9,-10,-11,-12,-13,-14,-5,17,-25,17,17,17,17,17,-15,]),'EQUALS':([1,2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[18,-1,-2,-6,-24,-3,-4,-7,18,18,18,18,18,18,-13,18,-5,18,-25,18,18,18,18,18,-15,]),'MINUS':([1,2,3,4,5,12,20,21,23,25,32,33,34,35,36,37,38,39,40,41,49,51,52,55,57,58,],[19,-1,-2,22,-6,-24,-3,-4,-7,19,-8,-9,-10,19,19,-13,-14,-5,19,-25,19,19,19,19,19,-15,]),'RPAREN':([2,3,5,12,20,21,23,25,32,33,34,35,36,37,38,39,41,49,51,52,57,58,],[-1,-2,-6,-24,-3,-4,-7,41,-8,-9,-10,-11,-12,-13,-14,-5,-25,-16,-17,-18,58,-15,]),'COMMA':([2,3,5,12,20,21,23,26,27,28,29,30,32,33,34,35,36,37,38,39,40,41,49,50,51,52,53,54,55,58,],[-1,-2,-6,-24,-3,-4,-7,43,-23,43,46,-20,-8,-9,-10,-11,-12,-13,-14,-5,48,-25,-16,-22,-17,-18,-19,-21,56,-15,]),'NUMBER':([4,22,],[21,39,]),'COLON':([12,26,27,28,29,30,50,53,54,],[-24,42,-23,44,45,-20,-22,-19,-21,]),'DIV':([12,31,],[-24,47,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'expr':([0,6,8,13,14,15,16,17,18,19,24,42,44,45,48,56,],[1,23,25,32,33,34,35,36,37,38,40,49,51,52,55,57,]),'name':([0,6,8,9,10,11,13,14,15,16,17,18,19,24,42,43,44,45,46,47,48,56,],[5,5,5,27,27,31,5,5,5,5,5,5,5,5,5,50,5,5,31,54,5,5,]),'number':([4,],[20,]),'names':([9,10,],[26,28,]),'subs':([11,],[29,]),'sub':([11,46,],[30,53,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> expr","S'",1,None,None,None),
  ('expr -> TRUE','expr',1,'p_bool','_parser.py',101),
  ('expr -> FALSE','expr',1,'p_bool','_parser.py',102),
  ('expr -> AT number','expr',2,'p_node','_parser.py',107),
  ('number -> NUMBER','number',1,'p_number','_parser.py',111),
  ('number -> MINUS NUMBER','number',2,'p_negative_number','_parser.py',115),
  ('expr -> name','expr',1,'p_var','_parser.py',120),
  ('expr -> NOT expr','expr',2,'p_unary','_parser.py',124),
  ('expr -> expr AND expr','expr',3,'p_binary','_parser.py',128),
  ('expr -> expr OR expr','expr',3,'p_binary','_parser.py',129),
  ('expr -> expr XOR expr','expr',3,'p_binary','_parser.py',130),
  ('expr -> expr IMPLIES expr','expr',3,'p_binary','_parser.py',131),
  ('expr -> expr EQUIV expr','expr',3,'p_binary','_parser.py',132),
  ('expr -> expr EQUALS expr','expr',3,'p_binary','_parser.py',133),
  ('expr -> expr MINUS expr','expr',3,'p_binary','_parser.py',134),
  ('expr -> ITE LPAREN expr COMMA expr COMMA expr RPAREN','expr',8,'p_ternary_conditional','_parser.py',139),
  ('expr -> EXISTS names COLON expr','expr',4,'p_quantifier','_parser.py',143),
  ('expr -> FORALL names COLON expr','expr',4,'p_quantifier','_parser.py',144),
  ('expr -> RENAME subs COLON expr','expr',4,'p_rename','_parser.py',149),
  ('subs -> subs COMMA sub','subs',3,'p_substitutions_iter','_parser.py',153),
  ('subs -> sub','subs',1,'p_substitutions_end','_parser.py',159),
  ('sub -> name DIV name','sub',3,'p_substitution','_parser.py',163),
  ('names -> names COMMA name','names',3,'p_names_iter','_parser.py',169),
  ('names -> name','names',1,'p_names_end','_parser.py',175),
  ('name -> NAME','name',1,'p_name','_parser.py',179),
  ('expr -> LPAREN expr RPAREN','expr',3,'p_paren','_parser.py',183),
]
