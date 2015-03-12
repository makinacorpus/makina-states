Devhost nodetype
================

This state will regiter and mark this minion as a **devhost**.

The devhost has the special meaning to marking the machine as a development box.

Currently, we associate some behaviors on development boxes like making postfix
& dovecot (mail) to be completly local.
We also will tweak some settings like in apache, php or mysql states when we are
in dev.


The idea when you have to test if you are on a development box is to test for
devhost in the registry::

    {{ salt['mc_nodetypes.registry']().is.devhost }}



