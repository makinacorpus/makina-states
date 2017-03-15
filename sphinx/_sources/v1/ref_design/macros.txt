Macros
========

**OBSOLETE** We know do not use any more base macros but access directly to salt execution modules, read some formulaes
to see in action.

Base macros
-----------
To access the registries and make a thin and easier higth level settings API, we use macros as importable modules inside the states files.
Thus, we have in _macros those macros:

    - :_macros/funcs.jinja: macro containing some helper functons
    - :_macros/localsettings.jinja: macro related to localsettings
    - :_macros/controllers.jinja: macro related to controllers
    - :_macros/nodetypes.jinja: macro related to nodetypes
    - :_macros/services.jinja: macro related to services

Utilities macros
-----------------
For certain complicated states, we have made some macros to leverage:

    - The use of those states in your own states files
    - The use of the settings themselves

The macros:

    - :_macros/apache.jinja: macro containing some helpers to make vhosts
    - :_macros/php.jinja: macro containing some helpers to make phpfpm pools
    - :_macros/salt.jinja: internal macros to configure all the salt infra.
 


