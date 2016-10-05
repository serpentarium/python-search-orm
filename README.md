# python-search-orm
Unified ORM for lucene based search engines. Should contain `QuerySet`, `ResultSet`, and Django-like `Q` objects, and be easy-to-use for declarative query construction.  

This package should/will contain only abstract logic that allows to build working search ORM.


----------
### TODO ###
 - `QuerySet` definition;
 - `ResultSet` definition;
 - `Tree.node` for search condition tree;
 - Common fields operations mixins. For  `QuerySet` and `Q` objects (`fulltext`, `numeric`, `datetime`, `geo`...);
 - Registering operations for fields;
 - `Q` objects with overloaded all operators, we need. ( `>=`, `in`, `!=`, etc...);
 - ...

###Contributing###
Feel free to add commit, issue, todo item etc...
Thanks for any help even advice!
###License [MIT](https://github.com/ubombi/python-search-orm/blob/master/LICENSE "MIT License")###

    