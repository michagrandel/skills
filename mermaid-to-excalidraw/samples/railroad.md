# Railroad (syntax) diagrams

```mermaid
railroad-ebnf-beta
title "Simple identifier"

letter = "a" | "b" | "c" ;
digit = "0" | "1" | "2" ;
identifier = letter ( letter | digit | "_" )* ;
```

Optional groups, repetition, and alternatives:

```mermaid
railroad-ebnf-beta
title "Catalog query"

query = "find" term filter? sort? ;
term = letter+ ;
filter = "where" field operator value ;
sort = "sort by" field ("asc" | "desc")? ;
field = "name" | "tag" | "format" ;
operator = "=" | "contains" ;
value = letter+ ;
letter = "a" | "b" | "c" ;
```
