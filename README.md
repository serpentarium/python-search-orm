# python-search-orm
Unified ORM for lucene based search engines. Should contain `QuerySet`, `ResultSet`, and Django-like `Q` objects, and be easy-to-use for declarative query construction.  

This package should/will contain only abstract logic that allows to build working search ORM.


----------
### TODO ###
 - [x] `QuerySet` definition;
 - [x] `Q` objects with overloaded all operators, we need. ( `>=`, `in`, `!=`, etc...);
 - [x] Make some model fields magic, to generate `Q` from them.
 - [x] Auto-unpack iterbles `*Article.tags << ['tag1', 'tag2', 'tag3']` - tag1 in tags or tag2 in tags...
 - [x] Replace Q.__contains__ with something working. `<<` and reversed `>>`
 - [ ] `ResultSet` definition;
 - [ ] Common fields operations mixins. For  `QuerySet` and `Q` objects (`fulltext`, `numeric`, `datetime`, `geo`...);
 - [ ] Registering operations for fields;
 - [ ] Multi-model search. Within one schema/core.
 - [ ] Clean code.
 - [ ] Make setup.py.
 - [ ] Make docs.
 - [ ] ...
 - [ ] Finish TODO section

###Contributing###
Feel free to add commit, issue, todo item etc...
Thanks for any help even advice!
###License [MIT](https://github.com/ubombi/python-search-orm/blob/master/LICENSE "MIT License")###

    
