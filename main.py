from dataclasses import dataclass
import re
import sys
from typing import Optional

class component:
    def apply_rec(self, arg, bind_level = -1):
        '''
        1. find the variables bound under `bind_level` bindings (n == bind_level)
        2. replace the variables with the argument, with the free variables shifted
        '''
        pass
    def shift(self, amount, bind_level = -1):
        'increment the free variables in the expression (n >= `bind_level`) by `amount`'
        pass
    def reify(): pass
    def reduce1(self, is_head = False):
        '''
        reduces the component once, returning None if no reduction is possible.
        if component has a side effect, activates it
        '''
        # if is_head and self.msg is not None: print(self.msg)
    def reduce(self):
        'reduces the component into normal form'
        res = self
        while (self := self.reduce1()): res = self
        return res

@dataclass
class index(component):
    num: int
    def apply_rec(self, arg, bind_level=-1):
        if self.num == bind_level: return arg.shift(bind_level) # replace referenced variable
        if self.num > bind_level: return index(self.num - 1) # decrement free variable
        return self # bound variable unchanged
    def shift(self, amount, bind_level=-1):
        if self.num > bind_level: return index(self.num + amount) # shift free variable
        return self # bound variable unchanged

    def __str__(self):
        return str(self.num)
    def __repr__(self):
        return str(self.num)

@dataclass
class group(component):
    body: tuple
    redux: bool
    msg: Optional[str]
    def __init__(self, *body, redux=True, msg=None):
        self.body, self.redux, self.msg = body, redux, msg
    def apply_rec(self, arg, bind_level=-1):
        return group(*(x.apply_rec(arg, bind_level) for x in self.body), redux=self.redux)
    def shift(self, amount, bind_level=-1):
        return group(*(x.shift(amount, bind_level) for x in self.body), redux=self.redux)
    def reduce1(self):
        # super().reduce1()
        if self.msg is not None:
            print(self.msg, end='')
            return lda(*self.body)

        T = type(self)
        if len(self.body) == 0: raise ValueError('empty group')
        # singleton group reduces to its element
        if len(self.body) == 1 and T is group: return self.body[0]
        # groups are unnecessary at the beginning of a group body
        if type(self.body[0]) is group and self.body[0].redux:
            return T(*self.body[0].body, *self.body[1:])
        
        # if a lamba is at the head, it can be applied to group
        if len(self.body) >= 2 and isinstance(self.body[0], lda):
            lamb = self.body[0]
            arg = self.body[1]
            return T(lamb.apply(arg), *self.body[2:])
        
        # if a reducible group is anywhere in the head, reduce it
        for i, sub in enumerate(self.body):
            if isinstance(sub, group) and sub.redux and (red := sub.reduce1()):
                return T(*self.body[:i], red, *self.body[i+1:])
        else: return None
    def __str__(self):
        if self.redux: return f"({stringify_expression(self.body)})"
        return f"[{stringify_expression(self.body)}]"
    def __repr__(self):
        if self.redux: return f'({" ".join(repr(x) for x in self.body)})'
        return f'[{" ".join(repr(x) for x in self.body)}]'


@dataclass
class lda(group):
    # body: tuple
    def __init__(self, *body, msg=None):
        super().__init__()
        self.body = body; self.msg = msg
    def apply_rec(self, arg, bind_level=-1):
        return lda(*super().apply_rec(arg, bind_level + 1).body, msg=self.msg)
    def apply(self, arg):
        return group(*self.apply_rec(arg).body, msg=self.msg)
    def shift(self, amount, bind_level=-1):
        return lda(*super().shift(amount, bind_level + 1).body)
    def __str__(self):
        if self.msg is not None: return f"\"λ {stringify_expression(self.body)}"
        return f"λ {stringify_expression(self.body)}"
    def __repr__(self):
        if self.msg is not None: return f"\"λ {' '.join(repr(x) for x in self.body)};"
        return f"λ {' '.join(repr(x) for x in self.body)};"

@dataclass
class identifier(component):
    id: str
    def reify():
        raise NotImplementedError()
    def apply_rec(self, arg, bind_level=-1):
        return self.reify().apply(arg, bind_level)
    def shift(self, amount, bind_level=-1):
        return self.reify().shift(amount, bind_level)
    def reduce1(self):
        super().reduce1()
        return self.reify()
    def __str__(self):
        return self.id
    def __repr__(self):
        return f'<{self.id}>'

def stringify_expression(expression):
    out = ''
    for x in expression[:-1]:
        if type(x) is lda: out += '(' + str(x) + ')'
        else: out += str(x)
        out += ' '
    out += str(expression[-1])
    return out

def read_components(str):
    'parses a string, returns a tuple of `component`s'
    out = list()
    str = str.lstrip()
    while len(str) > 0:
        comp, l = read_component_len(str)
        out.append(comp)
        str = str[l:].lstrip()
    return tuple(out)
def read_component(str): return read_component_len(str)[0]
def read_component_len(str):
    'parses string, returns a single `component` and the length of string consumed'
    str = str.lstrip()
    if len(str) == 0: raise Exception('empty string')
    if str[0] in '\\λ': return lda(*read_components(str[1:])), len(str) # lda
    elif str[0] in '([': # group
        open_brace = str[0]
        close_brace = {'(':')', '[':']'}[open_brace]
        level = 0
        for i, ch in enumerate(str):
            if ch == open_brace: level += 1
            elif ch == close_brace: level -= 1
            if level == 0: break
        else: raise Exception(f"unmatched '{open_brace}' brace")
        return group(*read_components(str[1:i])), i+1
    elif str[0] in '0123456789': # index
        match = re.match(r'[0-9]+', str)[0]
        return index(int(match)), len(match)
    elif str[0] == '"': # printer lda
        match = re.match(r'"([^"]|\\")*"', str)[0]
        message = unescape(match[1:-1])
        return lda(index(0), msg=message), len(match)
    else: # identifier
        if str[0] == '.':
            raise NotImplementedError()
        return identifier(str[0]), 1

def unescape(str):
    # TODO implement a more general unescaper
    str = str.replace(r'\n', '\n')
    str = str.replace(r'\r', '\r')
    str = str.replace(r'\\', '\\')
    str = str.replace(r'\"', '\"')
    str = str.replace(r'\'', '\'')
    str = str.replace(r'\t', '\t')
    return str

false = read_component(r'\\0')
successor = read_component(r'\\\1(210)')

c0 = group(*read_components(r'(\\1(1 0))(\\\1(2 1 0))\\1 0'))

# TODO extract into libs
def main():
    if len(sys.argv) < 2:
        print ('please supply program file')
    with open(sys.argv[1]) as file:
        program = file.read()
    ir = group(*read_components(program))
    ir = ir.reduce()
    print('rem:', ir)
def debug():
    with open('examples/hello-world') as file:
        program = file.read()
    ir = group(*read_components(program))
    ir = ir.reduce()
    print('rem:', ir)

DEBUG = True
if __name__ == '__main__':
    if DEBUG: debug()
    else: main()
