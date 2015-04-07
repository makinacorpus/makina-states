
Example of a project Creation
--------------------------------
- The first thing to do is to create a **nest** from your project::

    salt-call --local mc_project.deploy <your_project_name> # dont be long, dont use - & _

- This empty structure respects the corpus reactor layout, and is just an useless helloword.
  What you want to do is to hack something more serious inside.
  The project deployment proceudre waits for a **.salt** folder inside your project repository
  with enougth information on how to deploy it.

- You ll have to have at least

    - ``.salt/archive.sls``: archive step
    - ``.salt/fixperms.sls``: fixperm step
    - ``.salt/notify.sls``: notify step
    - ``.salt/PILLAR.sample``: configuration default values
    - ``.salt/rollback.sls``: rollback step

- To deploy your project, you can add as many SLSes as you want, and the ones directly in **.salt** will be executed in alphabetical order except the ones beginning with **task_**.

- Indeed the ones beginning with **task_** are mean to be either included by your other slses to factor code out or to be executed manually via the **run_task** command.

Those files are created during the initialisation, you can adapt them or take
the ones from a project helper or example that you can see on :ref:`projects_project_list`


- Basically, when doing a project you will:

    - create the deployment procedure and put something in **.salt**
    - hack your project
    - adapt the deployment project
    - reiterate



Additionnal docs
---------------------
You can refer to :ref:`module_mc_project_2`
