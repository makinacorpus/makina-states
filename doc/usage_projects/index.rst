.. _projects_intro:

Project lifecyle in Makina-States
=================================
The whole idea
-----------------
A project in makina-states is as simple a initing the project layout on the production system.
This is a one liner command (or API call).
After that, you push your code using only git to your production end point and makina-states handles
the deployment for you.
In other words, you get a repo for the pillar, one for your code + salt recipes,
and you push onto those remotes for your application to be deployed.

The whole stack is composed of saltstack, makina-states and corpus.

Specifications
------------------
See `corpus spec <https://github.com/makinacorpus/corpus.reactor/blob/master/doc/spec_v2.rst>`_

.. _projects_project_list:

Projects
--------------------

More generally, a research link: `Projects <https://github.com/makinacorpus?utf8=%E2%9C%93&query=corpus->`_
As the above lists are far from exhaustive.


Projects Exemples
+++++++++++++++++++
- `zope <https://github.com/makinacorpus/corpus-zope>`_
- `django <https://github.com/makinacorpus/corpus-django>`_
- `drupal <https://github.com/makinacorpus/corpus-drupal>`_
- `flask <https://github.com/makinacorpus/corpus-flask>`_

Helpers & resource projects
++++++++++++++++++++++++++++++
- `pgsql <https://github.com/makinacorpus/corpus-pgsql>`_
- `mysql <https://github.com/makinacorpus/corpus-mysql>`_
- `elasticsearch <https://github.com/makinacorpus/corpus-elasticsearch>`_
- `solr <https://github.com/makinacorpus/corpus-solr>`_
- `osmdb <https://github.com/makinacorpus/corpus-osmdb>`_
- `rabbitmq <https://github.com/makinacorpus/corpus-rabbitmq>`_
- `mongodb <https://github.com/makinacorpus/corpus-mongodb>`_

Additionnal topics
-------------------
.. toctree::
   :maxdepth: 2

   project_creation.rst
