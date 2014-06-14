Project lifecyle in Makina-States
=================================
The whole idea
-----------------
A project in makina-states is as simple a initing the project itself.
After that, you push your code using only git to your production end point and makina-states handles
the deployment for you.
In other words, you get a repo for the pillar, one for your code + salt recipes, 
and you push onto those remotes for your application to be deployed.

The whole stack is composed of saltstack, makina-states and corpus.


Specifications
------------------
See `corpus spec <https://github.com/makinacorpus/corpus.reactor/blob/master/doc/spec_v2.rst>`_

Exemples
----------

`zope <https://github.com/makinacorpus/corpus-zope>`_
    zope deployment
    
`osmdb <https://github.com/makinacorpus/corpus-osmdb>`_
    OpenStreetMap databases with minutediff deployment
    
`lizmap <https://github.com/makinacorpus/corpus-lizmap>`_
    A basic lizmap installation with qgist server & ftp uploads
    
`flask <https://github.com/makinacorpus/corpus-flask>`_
    A basic flask installation
    
`django <https://github.com/makinacorpus/corpus-django>`_
    A basic django installation    
    
`tilestream <https://github.com/makinacorpus/corpus-tilestream>`_ / *nodejs*
    A basic tilestream ( *nodejs* ) installation 

ckan
    (obsolete) A ckan installation

