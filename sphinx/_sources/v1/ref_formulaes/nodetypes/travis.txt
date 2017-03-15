TravisCI nodetype
=================

Mark this machine as a travis node.
Useful to skip some part of your states when you are limited by travis limitations like no setting sysctl and no supporting  posix acls.

To test if you are on a travis box::

    {{ salt['mc_nodetypes.registry']().is.travis }}



