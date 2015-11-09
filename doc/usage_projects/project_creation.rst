Project management
=====================


.. _project_creation:

Intro
--------------------------------
This page is the most important thing you ll have to read about makina-states as a **developer consumer**, take the time it needs and deserves.

Never be afraid to go read makina-states code, it will show you how to configure
and extend it. It is simple python and yaml.

See python exemples:

    - `the modules <https://github.com/makinacorpus/makina-states/tree/master/mc_states/modules>`_
    - `the states <https://github.com/makinacorpus/makina-states/tree/master/mc_states/states>`_
    - `the runners <https://github.com/makinacorpus/makina-states/tree/master/mc_states/runners>`_

See formulaes exemples:

    - `the localsettings <https://github.com/makinacorpus/makina-states/tree/master/localsettings>`_
    - `the services <https://github.com/makinacorpus/makina-states/tree/master/services>`_

Specifications
------------------
See the original spec on :ref:`project_corpus` .

Initialization
++++++++++++++++
- a project in corpus / makina-states is a git repository checkout which contains the code
  and a well known saltstack based procedure to deploy it
  from end to end in the **.salt** folder.
- By default the project procedure is done via a `masterless salt call <http://docs.saltstack.com/en/latest/topics/tutorials/quickstart.html>`_.
- The first thing to do is to create a **nest** from such a project, **IF IT IS NOT ALREADY DONE** (just ls /srv/projects to check)::

    salt-call --local mc_project.deploy <your_project_name> # dont be long, dont use - & _

- This empty structure respects the aforementioned corpus reactor anatomy, and is just an useless helloword project which should look like::

    /srv/projects/<your_project_name>
        |
        |- pillar/init.sls: override values in PILLAR.sample and define
        |                   any other arbitrary pillar DATA.
        |
        |- data/: anything which is persisted to disk must live here
        |         from drupal sites/default/files, python eggs, buildouts parts,
        |         gems cache, sqlite files, static files, docroots, etc.
        |
        |- project/ <- a checkout or your project
        |    |-  .git
        |    |-  codebase
        |    |-  .salt
        |        |- _{_modules,_states,_runners,_sdb, ...}: optional custom salt python modules to install
        |        |- PILLAR.sample
        |        |- task_foo.sls
        |        |- 00_deploy.sls
        |
        |- git/project.git: bare git repos synchronnized (bi-directional)
        |                   with project/ used by git push style deployment
        |- git/pillar.git:  bare git repos synchronnized (bi-directional)
                            with pillar/ used by git push style deployment


- What you want to do is to replace the ``project`` folder by your repo.
  This one contains your code, as asual, plus the **.salt** folder,
- **WELL Understand** what is :

    - a `salt SLS <http://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html#moving-beyond-a-single-sls>`_ , it is the nerve of the war.
    - the `Pillar of salt <http://docs.saltstack.com/en/latest/topics/tutorials/pillar.html>`.

- **be ware**, on the production server the ``.git/config`` is linked with the
  makina-states machinery and you cannot replace it blindly, you must use :ref:`git foo` to
  do it.
- Ensure to to have at least in your project git folder:

    - ``.salt/archive.sls``: archive step
    - ``.salt/fixperms.sls``: fixperm step
    - ``.salt/PILLAR.sample``: configuration default values to use in SLSes
    - ``.salt/rollback.sls``: rollback step

- You can then add as many SLSes as you want, and the ones directly in **.salt** will be executed in alphabetical order except the ones beginning with **task_** (task_foo.sls). Indeed the ones beginning with **task_** are different beasts and are intended to be either included by your other slses to factor code out or to be executed manually via the ``mc_project.run_task`` command.
- You can and must have a look for inspiration on :ref:`projects_project_list`

.. _git foo:

git foo
+++++++++

- The git foo that you will have do to replace the git folder and initialize your project
  if you do it directly on your server will look like::

      # go inside your project repo folder
      cd /srv/projects/<your_project_name>/project
      # download your project codebase from your forge
      git remote add g https://github.com/foo/foo.git
      git fetch --all
      # force checkout/reset the force code inside the local copy
      git reset --hard g/master
      # make the LOCAL remote counterpart in sync with the localcopy
      git push --force origin HEAD:master

- **REMINDER**: DONT MESS WITH THE **ORIGIN** REMOTE

Sumup
++++++++
To sum all that up, when beginning project you will:

- Initialize if not done a project structure with ``salt-call --local mc_project.deploy project``
- add a **.salt** folder alongside your project codebase (in it's git repo).
- deploy it, either by:

    - git push --force your **pillar** files to ``host:/srv/projects/project/git/pillar.git``
    - git push --force your **project code** to ``host:/srv/projects/project/git/project.git``
      (this last push triggers a deploy)

- or

    - edit/commit/push --force directly in ``host:/srv/projects/project/pillar``
    - edit/commit/push --force directly in ``host:/srv/projects/project``
    - Launch the ``salt-call --local mc_project.deploy <name> only=install,fixperms`` dance

- reiterate

Deploying, two ways of doing things
------------------------------------------
To build and deploy your project we provide two styles of doing style that should be appropriate for most use cases.

Either directly from the deployment host as root::

    # maybe you want to edit before deploy
    # vim pillar/init.sls
    # cd pillar;git comit -m foo;git push;cd ..
    # vim project/foo
    # cd project;git comit -m foo;git push;cd ..
    salt-call --local -ldebug mc_project.deploy <name> only=install,fixperms

Or only by pushing well placed git changesets, from your local box,

    - If needed on the pillar, it does not trigger a deploy
    - And on the project remote, it triggers here the deploy::

        git clone host:/srv/projects/project/git/pillar.git
        vim init.sls
        git commit -am up;git push
        git clone git@github.com/makinacorpus/myawsomeproject.git
        git remote add prod /srv/projects/project/git/project.git
        git fetch --all
        git push prod <mybranch>:master
        eg: git push prod <mybranch>:master
        eg: git push prod awsome_feature:master

The ``<branchname>:master`` is really important as everything in the production git repositories is wired on the master branch. You can push any branch you want from your original repository, but in production, there is only **master**.

SaltStack integration
--------------------------
As you know in makina-states, there are 2 concurrent salt installs, one for **salt**, the one that you use,
and one for **mastersalt** for the devil ops.
In makina-states, we use by default:

- a virtualenv inside ``/salt-venv/salt``
- `salt from a fork <https://github.com/makina-corpus/salt.git>`_ installed inside ``/salt-venv/salt/src/salt``
- the salt file root resides, as usual, in ``/srv/salt``
- the salt pillar root resides, as usual, in ``/srv/pillar``
- the salt configuration root resides, as usual, in ``/etc/salt``

As you see, the project layout seems not integration on those following folders, but in fact, the project
initialisation routines made symlinks to integrate it which look like::

    /srv/salt/makina-projects/<your_project_name>>  -> /srv/projects/<your_project_name>/project§/.salt
    /srv/pillar/makina-projects/<your_project_name> -> /srv/projects/<your_project_name>/pillar

- The pillar is auto included in the **pillar top** (``/srv/pîllar/top.sls``).
- The project salt files are not and **must not** be included in the salt **top** for further highstates unless
  you know what you are doing.

You can unlink your project from salt with::

    salt-call --local -ldebug mc_project.unlink <your_project_name>

You can link project from salt with::

    salt-call --local -ldebug mc_project.link <your_project_name>

Configuration variables
++++++++++++++++++++++++++
We provide in **mc_project** a powerfull mecanism to define default variables used in your deployments.
hat you can safely override in the salt pillar files.
This means that you can set some default values for, eg a domain name or a password, and input the production values that you won't commit along side your project codebase.

- Default values have to be stored inside the **PILLAR.sample** file.
- Some of those variables, the one at the first level are mostly read only and setup by makina-states itself.
  The most important are:

    - ``name``: project name
    - ``user``: the system user of your project
    - ``group``: the system group of your project
    - ``data``: top level free variables mapping
    - ``project_root``: project root absolute path
    - ``data_root``: persistent folder absolute path
    - ``default_env``: environment (staging/prod/dev)
    - ``pillar_root``: absolute path to the pillar
    - ``fqdn``: machine FQDN

- The enly variables that you can edit at the first level are:

    - **default_env**: environement (valid values are staging/dev/prod)
    - **env_defaults**: indexed by **env** dict that overloads data (pillar will still have the priority)
    - **os_defaults**: indexed by **os** dict that overloads data (pillar will still have the priority)

- The other variables, members of the **data** sub entry are free for you to add/edit.
- Any thing in the pillar (``pillar/init.sls``) overloads what is in ``project/.salt/PILLAR.sample``.

So, we have a data structure with at least 2 levels, the second level is only starting from the **data** key.

You can get and consult the result of the configuration assemblage like this::

    salt-call --local -ldebug mc_project.get_configuration <your_project_name>


Example

in ``project/.salt/PILLAR.sample``, you have:

    makina-projects.projectname:
      data:
        start_cmd: 'myprog'


in ``pillar/init.sls``, you have:

    makina-projects.projectname:
      data:
        start_cmd: 'myprog2'

- In your states files, you can access the configuration via the magic ``opts.ms_project`` variable.
- In your modules or file templates, you can access the configuration via ``salt['mc_project.get_configuration'(name)``.
- A tip for loading the configuration from a template is doing something like that:

.. code-block:: yaml

    # project/.salt/00_deploy.sls
    {% set cfg = opts.ms_project %}
    toto:
      file.managed:
          - name: "source://makina-projects/{{cfg.name}}/files/etc/foo"
          - target: /etc/foo
          - user {{cfg.user}}
          - group {{cfg.user}}
          - defaults:
              project: {{cfg.name}}

    # project/.salt/files/etc/foo
    {% set cfg = opts.ms_project %}
    My Super Template of {{cfg.name}} will run {{cfg.data.start_cmd}}

Filesystem considerations
--------------------------
We use `POSIX Acls <http://en.wikipedia.org/wiki/Access_control_list#Filesystem_ACLs>`_ in
various places on your project folders.
At first, it feels a bit complicated, but it will enable you to smoothlessly edit your files or run
your programs with appropriate users without loosing security.

Related topics
---------------------
You can refer to :ref:`module_mc_project_2`
