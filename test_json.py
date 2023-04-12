from queue import Queue

from lark import Discard, Lark

json_grammar = r"""
    ?start: "[" [command ("," command)*] "]"
    command: value

    ?value: object
          | array
          | string
          | SIGNED_NUMBER      -> number
          | "true"             -> true
          | "false"            -> false
          | "null"             -> null

    array  : "[" [value ("," value)*] "]"
    object : "{" [pair ("," pair)*] "}"
    pair   : string ":" value

    string : ESCAPED_STRING

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS

    %ignore WS
"""


class Transformer:
    def __init__(self, callback):
        self.callback = callback

    def command(self, children):
        print(children)
        self.callback(children[0])
        return Discard


def iter_parser(*args, transformer, **kwargs):
    queue = Queue()
    if not kwargs.setdefault("parser", "lalr") == "lalr":
        raise ValueError("The lalr parser is required")
    kwargs['transformer'] = transformer(queue.put)
    parser = Lark(*args, **kwargs)

    def parse(text, start=None):
        interactive = parser.parse_interactive(text, start)
        token = None
        for token in interactive.iter_parse():
            while not queue.empty():
                yield queue.get()
        interactive.feed_eof(token)
        while not queue.empty():
            yield queue.get()
    return parse


p = iter_parser(json_grammar, parser="lalr", transformer=Transformer)

test_text = """
[
 {
 "command": "print", "args": 
 ["argument", 0, {"some": "object"}]
 },
 {"command": 
 "input", "args": ["some prompt"]
 }
]
"""

for c in p(test_text):
    print("got", c)