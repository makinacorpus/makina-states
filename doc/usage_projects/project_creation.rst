
.. _project_creation:

Example of a project workflow
--------------------------------
Initialization
++++++++++++++++
- a project in corpus / makina-states is a git repository checkout which contains the code
  and a well known saltstack based procedure to deploy it
  from end to end in the **.salt** folder.
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
        |        |- archive.sls fixperms.sls notify.sls rollback.sls
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
- **WELL Understand** what is a `salt SLS <http://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html#moving-beyond-a-single-sls>`_ , it is the nerve of the war.
- **be ware**, on the production server the ``.git/config`` is linked with the
  makina-states machinery and you cannot replace it blindly, you must use :ref:`git foo` to
  do it.
- Ensure to to have at least in your project git folder:

    - ``.salt/archive.sls``: archive step
    - ``.salt/fixperms.sls``: fixperm step
    - ``.salt/notify.sls``: notify step
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

Configuration variables
--------------------------
We provide in **mc_project** a powerfull mecanism to define default variables used in your deployments, that you can safely override in the salt pillar files. This means that you can set some default values for eg a domain name or a password, and input the production values that you won't commit inside your project codebase.

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

Related topics
---------------------
You can refer to :ref:`module_mc_project_2`
