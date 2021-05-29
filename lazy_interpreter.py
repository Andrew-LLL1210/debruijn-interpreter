
def increment(obj, y, level):
    if type(obj) is int: return obj + y
    if type(obj) is printer: return obj
    t = type(obj)
    obj = list(obj)
    for i, x in enumerate(obj):
        if type(x) is group:
            obj[i] = group(increment(x, y, level))
        elif type(x) is lda:
            obj[i] = lda(increment(x, y, level + 1))
        elif type(x) is int and x > level:
            obj[i] = x + y
    return t(obj)

def replace_in(obj, y, level):
    obj = list(obj)
    for i, x in enumerate(obj):
        if type(x) is group:
            obj[i] = group(replace_in(x, y, level))
        elif type(x) is lda:
            obj[i] = lda(replace_in(x, y, level + 1))
        elif x == level:
            obj[i] = increment(y, x + 1, 0)
    return obj

class lda(tuple):
    def __repr__(self):
        return repr(list(self))
    def __call__(self, y):
        return group(increment(replace_in(self, y, 0), -1, 0))
class group(tuple): pass
class printer(str):
    def __call__(self, y):
        print(self, end='')
        return y
    
from codecs import encode, decode
def unescape(sample):
    return decode(encode(sample, 'latin-1', 'backslashreplace'), 'unicode-escape')

replace = {}

def deBruijn(string):
    def loop(src, dest, is_lda=False):
        for ch in src:
            if ch in 'λ\\':
                new_lda = []
                flag = loop(src, new_lda, True)
                dest.append(lda(new_lda))
                if flag: return True
            elif ch in '([':
                new_grp = []
                loop(src, new_grp)
                dest.append(group(new_grp))
            elif ch in ')]':
                return is_lda
            elif ch in '0123456789':
                dest.append(int(ch))
            elif ch == '"':
                dest.append(printer(unescape(string_loop(src))))
            elif not ch in " \n\t\r":
                if ch in replace:
                    dest.append(replace[ch])
                else:
                    new_dict_entry = []
                    loop(src, new_dict_entry)
                    new_dict_entry = group(new_dict_entry)
                    replace[ch] = new_dict_entry
    def string_loop(src):
        string = ''
        for ch in src:
            if ch == '"': return string
            string += ch
            if ch == '\\': string += next(src)
    a = []
    loop(iter(string), a)
    return group(a)

def exec(progm):
    if type(progm) is not group: return progm
    ls = list(progm)
    while True:
        if type(ls[0]) is group:
            ls = list(ls[0]) + ls[1:]
        elif len(ls) == 1:
            if type(ls[0]) is not group: return ls[0]
            ls = list(ls[0])
        else:
            ls[0] = ls[0](ls.pop(1))
    return group(ls)


import sys

def exec_file(file, args):
    with open(file) as file:
        source = file.read()

    progm = exec(deBruijn(source))

    for arg in args:
        progm = exec(progm(deBruijn(arg)))

if __name__ == '__main__':
    exec_file(sys.argv[1], sys.argv[2:])