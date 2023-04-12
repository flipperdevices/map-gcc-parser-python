from lark import Lark, tree

grammar = r'''
// DISCARD 
// *(COMMON) 
// OUTPUT 
// size before relaxing 
//  *(SORT_BY_NAME(.init_array.*)) 
 
?start: section_object+ 
 
 
?section_object: "\n" section_name (" "+ | "\n" ) useless_meta* subsection+ -> section_object 
 
?useless_meta: " " (" " | VALID_STRING)+ "\n" 
?section_name: VALID_STRING -> section_name 
 
?subsection: subsection_header* (" " object | fill_data) -> subsection 
 
// refactor VALID_HEADER_STRING *(*()) etc 
?subsection_header: " *" VALID_HEADER_STRING* "(" (VALID_HEADER_STRING | " ")+ ")" "\n" -> subsection_header 
 
?fill_data: " *fill*" " "+ address " "+ size " "* ["\n"] (" "+ subobject)* -> fill_data 
// fill example 
//  *fill*         0x00000000200005d1        0x3  
//                 0x00000000200005d4                _edata = . 
 
NEW_LINE: /\n/ 
DELIMITER: " "+  
 
// ?section: section_object object+ 
// ?section_object: subgroup address size  
?object: subgroup ["\n"] " "+ address " "+ size  " "+ (file_name | module_name  "("file_name")") ["\n"]  (" "+ subobject)*  
// or to avoid invalid strings like .test.   
// ?object: subgroup DELIMITER address DELIMITER size DELIMITER (module_name | file_name)   
  
?subobject:  address " "+ DEMANGLED_NAME ["\n"] 
  
?subgroup: ([DOT] NAME)+  
?module_name: /[\w\-\/\+\.]+\.a/ -> module_name 
?file_name: /[\w\-\/\+\.]+\.o/ -> file_name 
 
VALID_HEADER_STRING: /[\w\d\/\-\=\.\*\:]+/ 
VALID_STRING: /[\w\d\/\-\=\.\(\)\+]+/ 
DEMANGLED_NAME: /[^ ][\w\-\=\. \(\)\+\:\~\*\,\$\&\<\>]+/   
ARCHIVE_EXTENSION: ".a"  
OBJECT_EXTENSION: ".o"  
  
// DELIMITER: " "+  
   
DOT: "."   
   
?address: HEX_NUMBER -> address   
   
?size: HEX_NUMBER -> size   
   
HEX_NUMBER : "0x" HEXDIGIT+   
 
FILE_PATH: /[\w\-\/\+\.\]+o/  
NAME: /[^\W][\w\-]*/  
   
%import common.HEXDIGIT   
%import common.WS   
// %ignore DELIMITER  
// %ignore WS   
// %ignore NEW_LINE 
// %ignore NEW_LINE 
%import common.CNAME   
%import common.NUMBER   
%import common.ESCAPED_STRING   
%import common.WORD   
%import common.WS_INLINE   
   
// %ignore WS_INLINE   
   
//.isr_vector   
// .isr_vector    0x0000000008000000      0x13c build/f7-firmware-D/lib/libflipper7.a(startup_stm32wb55xx_cm4.o)   
//                 0x0000000008000000                g_pfnVectors
'''


parser = Lark(grammar, parser='earley')
self_contents = open("firmware1.txt").read()
tree = parser.parse(self_contents+'\n')
print(tree)
# tree.pydot__tree_to_png(parser.parse(self_contents+'\n'), 'filename.png')

# print(tree)