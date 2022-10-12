from dataclasses import dataclass
import re
import sys
from typing import Optional

class component:
    def apply(self, arg, bind_level = -1):
        '''
        1. find the variables bound under `bind_level` bindings (n == bind_level)
        2. replace the variables with the argument, with the free variables shifted
        '''
        pass
    def shift(self, amount, bind_level = -1):
        'increment the free variables in the expression (n >= `bind_level`) by `amount`'
        pass
    def reify(): pass

@dataclass
class index(component):
    num: int
    def apply(self, arg, bind_level=-1):
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
    irriducible: bool
    def __init__(self, *body, irriducible=False):
        self.body, self.irriducible = body, irriducible
    def apply(self, arg, bind_level=-1):
        return group(*(x.apply(arg, bind_level) for x in self.body), irriducible=self.irriducible)
    def shift(self, amount, bind_level=-1):
        return group(*(x.shift(amount, bind_level) for x in self.body), irriducible=self.irriducible)
    def __str__(self):
        if self.irriducible: return f"[{stringify_expression(self.body)}]"
        return f"({stringify_expression(self.body)})"
    def __repr__(self):
        if self.irriducible: return f'[{" ".join(repr(x) for x in self.body)}]'
        return f'({" ".join(repr(x) for x in self.body)})'


@dataclass
class lda(group):
    body: tuple
    message: Optional[str]
    def __init__(self, *body, message=None):
        super().__init__()
        self.body = body; self.message = message
    def apply(self, arg, bind_level=-1):
        return lda(*super().apply(arg, bind_level + 1).body)
    def shift(self, amount, bind_level=-1):
        return lda(*super().shift(amount, bind_level + 1).body)
    def to_group(self): return group(*self.body)
    def __str__(self):
        return f"λ {stringify_expression(self.body)}"
    def __repr__(self):
        return f"λ {' '.join(repr(x) for x in self.body)};"

@dataclass
class identifier(component):
    id: str
    def reify():
        raise NotImplementedError()
    def apply(self, arg, bind_level=-1):
        return self.reify().apply(arg, bind_level)
    def shift(self, amount, bind_level=-1):
        return self.reify().shift(amount, bind_level)
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
    else: # identifier
        if str[0] == '.':
            raise NotImplementedError()
        return identifier(str[0]), 1

false = read_component(r'\\0')
successor = read_component(r'\\\1(210)')

def reduce_once(comp):
    'returns None if no reduction is possible, otherwise returns the reduced component'
    if not isinstance(comp, component): raise TypeError('component required')
    
    if isinstance(comp, group):
        T = type(comp)

        if len(comp.body) == 0: raise ValueError('empty group')
        # singleton group reduces to its element
        if len(comp.body) == 1 and T is group: return comp.body[0]
        # groups are unnecessary at the beginning of a group body
        if type(comp.body[0]) is group and not comp.body[0].irriducible:
            return T(*comp.body[0].body, *comp.body[1:])
        
        # if a lamba is at the head, it can be applied to group
        if len(comp.body) >= 2 and isinstance(comp.body[0], lda):
            lamb = comp.body[0]
            arg = comp.body[1]
            return T(lamb.apply(arg).to_group(), *comp.body[2:])
        
        # if a reducible group is anywhere in the head, reduce it
        for i, sub in enumerate(comp.body):
            if isinstance(sub, group) and not sub.irriducible and (red := reduce_once(sub)):
                return T(*comp.body[:i], red, *comp.body[i+1:])
        else: return None
    elif isinstance(comp, identifier): return comp.reify()
    else: return None

def reduce_max(comp):
    res = comp
    while (comp := reduce_once(comp)): res = comp
    return res

# print(false)
c0 = group(*read_components(r'(\\1(1 0))(\\\1(2 1 0))\\1 0'))

# TODO extract into libs
def main():
    if len(sys.argv) < 2:
        print ('please supply program file')
    with open(sys.argv[1]) as file:
        program = file.read()
    ir = group(*read_components(program))
    ir = reduce_max(ir)
    print('rem:', ir)

if __name__ == '__main__': main()
