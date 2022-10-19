# debruijn-interpreter

A python interpreter for my esolang DeBruijn

See the [Esolang Wiki page][page] for more information on DeBruijn

## Language Semantics

### Overview

The language DeBruijn is based off of a notation called the [De Bruijn Index][wikip],
used for representing terms of lambda calculus. Notably, DeBruijn uses 0-based indices,
so that the K-combinator or lambda calculus is written `λ λ 1`, not `λ λ 2`. The terms
may also be written with backslahes instead of Greek letter lambas: `\ \ 1`.

The principal purpose of a DeBruijn program is to simplify a lambda expression into
reduced normal form (although it may perform IO on the way). The program

```debruijn
(\ \ 3 1 (\ 0 2)) (\ 4 0)
```

when fed to the interpreter will give this output:

```shell
$ debruijn example1
rem: λ 2 (λ 5 0) λ 0 λ 6 0
```

Or as another example:

```debruijn
(\\1 (1 0))(\\\1 (2 1 0))(\\1 0)
```

```shell
$ debruijn example2
rem: λ λ 1 (1 (1 0))
```

Output may be performed via "dirty" lambdas

```debruijn
"hello world\n"
```

```shell
$ debruijn hello-world
hello world
rem: λ 0
```

[page]: https://esolangs.org/wiki/DeBruijn
[wikip]: https://wikipedia.org/wiki/de_bruijn_index
