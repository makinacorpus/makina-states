---
title: Usage
tags: [reference, projects]
weight: 2000
menu:
  main:
    parent: reference_projects
    identifier: reference_projects_usage
---

## Specification
- A project in **corpus / makina-states** is a **git repository** checkout
  which contains the code and <br/>
  a well known saltstack based procedure
  to deploy it from end to end in the **.salt** folder.
- Bear in mind the [project layout](/reference/projects/usage/#structure)
- You may have a look to the (now outdatedà original [project\_corpus](/reference/projects/RFC/) specification
- A good sumup of the spec is as follow:
    - There is a separate repo distributed along the project named
      **pillar** to store configuration variables, passwords and so on.
    - Projects are deployed via instructions based on saltstack which
      are contained into the **.salt** folder along the codebase.
- Projects can be deployed in two modes:
    - via a git push on a local, separated git repository where some hooks are wired to launch the deployment
    - If no remotes, deploy the code source we have locally
- The deployment folder, `.salt`, that you will provide along your codebase will describe how to deploy your project.
    - Deployment consist in ``META`` deployment phases:
        - **archive** `.salt/archive.sls`: synchronnise the project to the ``archive`` folder before deploying
        - **sync code** from remotes if there are remotes: if any remotes, synchronise both the pillar and the project
          git folder to their corresponding checkouted working copies
        - **sync/install custom salt modules** (exec, states, etc) from the codebase if any from the ``.salt`` folder
        - **fixperms** (`.salt/fixperms.sls`): enforce filesystem permissions
        - **install** (`.salt/install.sls`): Run project deployment procedure
            - Run any ``sls`` in the `.salt` folder (alphanum sorted) which:
                - Is not a main procedure sls
                - Is not a task (beginning with `task`
            - the convention is to name them `\d\d\d_NAME.sls`  (`000_prereqs.sls`)
        - **fixperms** (`.salt/fixperms.sls`): enforce filesystem permissions
        - **rollback** (`.salt/rollback.sls`): if error, rollback procedure (by default sync from `archived` folder
        - **notify** OPTIONNAL/LEGACY (`.salt/notify.sls`): after deployment, notify commands
- All other sls found at **toplevel** of the ``.salt`` folder  which are not those ones are
  executed in lexicographical order (alphanum) and
- The `.salt/PILLAR.sample` file contains default configuration variable for
  your project and helps you to know what variable to override in your
  custom pillar.

### Structure
- This empty structure respects the aforementioned corpus reactor
  layout, and is just an useless helloword project which should look like:

    ```
    /srv/projects/<project_name>
        |
        |- pillar/init.sls: override values in PILLAR.sample and define
        |                   any other arbitrary pillar DATA.
        |
        |- data/: anything which is persisted to disk must live here
        |         from drupal sites/default/files, python eggs, buildouts parts,
        |         gems cache, sqlite files, static files, docroots, etc.
        |
        |- project/ <- a checkout or your project
        |   |-  .git
        |   |-  codebase
        |   |-  .salt
        |     |- _modules : custom salt python exec modules
        |     |- _states  : custom salt python states modules
        |     |- _runners : custom salt python runners modules
        |     |- _...
        |     |
        |     |- PILLAR.sample
        |     |- task_foo.sls
        |     |- 00_deploy.sls
        |
        [ If "remote_less" is False (default)
        |- git/project.git: bare git repos synchronnized (bi-directional)
        |                   with project/ used by git push style deployment
        |- git/pillar.git:  bare git repos synchronnized (bi-directional)
        |                   with pillar/ used by git push style deployment
        |
        |- arhives/ <- past deployment archive folders
        |     |- <U-U-I-D1>
        |     |- <U-U-I-D2>
    ```

- What you want to do is to replace the `project` folder by your repo.<br/>
  This one contains your code, as asual, plus the **.salt** folder.
- **WELL Understand** what is :
    - a [salt SLS](http://docs.saltstack.com/en/latest/topics/tutorials/starting_states.html#moving-beyond-a-single-sls), it is the nerve of the war.
    - the [Pillar of salt](http://docs.saltstack.com/en/latest/topics/tutorials/pillar.html).
    - **be ware**, on the production server the `.git/config` is linked
      with the makina-states machinery, **NEVER MESS WITH ORIGIN AND MASTER BRANCH**.
- Ensure to to have at least in your project git folder:
    -   `.salt/PILLAR.sample`: configuration default values to use in
        SLSes
    -   `.salt/archive.sls`: archive step
    -   `.salt/fixperms.sls`: fixperm step
    -   `.salt/rollback.sls`: rollback step
- You can then add as many SLSes as you want, and the ones directly in
  **.salt** will be executed in alphabetical order except the ones
  beginning with **task\_** (task\_foo.sls). Indeed the ones beginning
  with **task\_** are different beasts and are intended to be either
  included by your other slses to factor code out or to be executed
  manually via the `mc_project.run_task` command.
- You can and must have a look for inspiration on [project templates](/reference/templates/)


## Deployment workflows
- To build and deploy your project we provide two styles of doing style
  that should be appropriate for most use cases.
    - [A local build workflow](/reference/projects/usage/#the-local-build-workflow)
    - [A distant git-push style workflow](/projects/usage/#the-git-push-to-prod-deploy-workflow)

### The local build workflow
- INITIALLY:
    - use `mc_project.init_project` to create the structure to host your project
    - use `mc_project.report` to verify things are in place
- Then
    - Edit/Place code in the pillar  folder: `/srv/projects/<project>/pillar` to configure the project
    - Edit/Place code in the project folder: `/srv/projects/<project>/project` and manually launch the deploy
- Wash, Rince, Repeat

### The git push to prod deploy workflow
- INITIALLY:
    - use `mc_project.init_project` to create the structure to host your project
    - use `mc_project.report` to verify things are in place
- Then
    - git push/or edit then push the pillar `host:/srv/projects/<project>/git/pillar.git` to configure the project
    - git push/or edit then push the code inside `host:/srv/projects/<project>/git/project.git` which triggers the deploy
- Wash, Rince, Repeat


## Deployment stategy
- To sum all that up, when beginning a project you will:
    - Initialize if not done a project structure with<br/>
      `salt-call mc_project.init_project project`
        - If you do not want git remotes, you can alternativly use<br/>
          `salt-call mc_project.init_project project remote_less=true`
    - add a **.salt** folder alongside your project codebase (in it's
      git repo).
    - deploy it, either by:
        - In **remote_less=True** mode or connected to the remote host to deploy onto:
              - edit/commit/push in `host:/srv/projects/<project>/pillar`
              - edit/commit/push/push to force in `host:/srv/projects/<project>/project`
              - Launch the `salt-call mc_project.deploy <project> only=install,fixperms,sync_modules` dance
        - In **remote_less=False** mode:
            - git push your **pillar** files to<br/>
              `host:/srv/projects/<project>/git/pillar.git`
            - git push your **project code** to<br/>
              `host:/srv/projects/<project>/git/project.git`<br/>
              (this last push triggers a deploy on the remote server)
            - Your can use `--force` as the deploy system only await the
              `.salt` folder. As long as the folder is present of the
              working copy you are sending, the deploy system will be happy.
- Wash, Rince, Repeat

## Initialize the project layout
- The first thing to do when deploying a project is to create a **nest** from it:<br/>
  **IF IT IS NOT ALREADY DONE** (just `ls /srv/projects` to check):

    ```sh
   bin/salt-call --local --retcode-passthrough -lall mc_project.init_project \
        <project_name> \
        [remote_less=false/true]
    ```
    - Dont be long, and dont use ``-`` & ``_`` for the `project name`
    - (opt) `remote_less` instructs to deploy with or without the git
      repos that allow users to use (or not) a **git push to prod to deploy** workflow.
        - If `remote_less=true`, the git repos wont be created, and you
          will have to use only the the ``local build workflow``.
        - If `remote_less=false`, you can use both the ``local build workflow``
          and the ``git push to prod deploy workflow``.
    - `--local -lall` instructs to run in masterless mode and extra verbosity
    - `mc_project.init_project $project` instructs to create the layout of
      the name `$project` project living into `/srv/projects/$project/project`

## Running deployment procedure
- The following command is the nerve of the war:

    ```sh
    bin/salt-call --local --retcode-passthrough -lall \
         mc_project.deploy $project\
          [only=step2[,step1]] \
          [only_steps=step2[,step1]]
    ```

- `mc_project.deploy $project` instructs to deploy the name `$project`
  project living into `/srv/projects/$project/project`
- (opt) `only` instructs to execute only the named global phases, and
  when deploying directly onto a machine, you will certainly have to
  use `only=install,fixperms,sync_modules` to avoid the
  archive/sync/rollback steps.
- (opt) `only_steps` instruct to execute only a specific or multiple
  specific sls from the **.salt** folder during the **install** phase.


## Tutorial

### Projects reminder tool
- **WARNING**: you can use it only if you provisionned your project
  with attached remotes (the default)
- Remember use the remotes inside `/srv/projects/<project>/git` and
  not directly the working copies
- If you push on the pillar, it does not trigger a deploy
- If you push on the project, it triggers the full deploy procedure
  including archive/sync/rollback.
- To get useful push informations, on the remote server to deploy to,
  just do

    ```sh
    salt-call -lall mc_project.report
    ```

### Using local build workflow
- [install makinastates](/install)
- Initialise the layout (only the first time)

    ```sh
    ssh root@remoteserver
    export project="foo"
    salt-call mc_project.init_project $project remote_less=true
    ```

- Edit the pillar

    ```sh
    cd /srv/projects/$project/pillar
    $EDITOR init.sls
    git commit -am up
    ```

- Add your project code

    ```sh
    export project="foo"
    cd /srv/projects/$project/project
    # if not already done, add your project repo remote
    git remote add o https://github.com/o/myproject.git
    # in any cases, update your code
    git fetch --all
    git reset --hard remotes/o/<the branch to deploy>
    ```

- Run the deployment procedure, **skipping archive/rollback** as you are connected and live editing

    ```sh
    salt-call mc_project.deploy $project only=install,fixperms,sync_modules
    # or to deploy only a specific sls
    salt-call \
        mc_project.deploy $project \
        only=install,fixperms,sync_modules only_steps=000_foo.sls
    ```

- When you want to commit your changes

    ```sh
    export project="foo"
    cd vms/VM/srv/$project/project
    git push o HEAD:<master> # replace master by the branch you want to push
                             # back onto your forge
    ```


### Using git push to prod deploy workflow
- [install makinastates](/install)
- The following lines edit the pillar, and push it, this does not trigger a deploy

    ```sh
    cd $WORKSPACE/myproject
    git clone host:/srv/projects/project/git/pillar.git
    $EDITOR pillar/init.sls
    cd pillar;git commit -am up;git push;cd ..
    ```

- The following lines prepare a clone of your project codebase to be able
 to be deployed onto production or staging servers

    ```sh
    cd $WORKSPACE/myproject
    git clone git@github.com/makinacorpus/myawsomeproject.git
    git remote add prod /srv/projects/project/git/project.git
    git fetch --all
    ```

- To trigger a remote deployment, now you can do:

    ```sh
    git push [--force] prod <mybranch>:master
    eg: git push [--force] prod <mybranch>:master
    eg: git push [--force] prod awsome_feature:master
    ```

- **REMINDER**:
    - DONT MESS WITH THE **ORIGIN** REMOTE when your are connected
      to your server in any of the `pillar` or
      `project` directory..
    - The `<branchname>:master` is really important as everything
      in the production git repositories is wired on the `master`
      branch. You can push any branch you want from your original
      repository, but in production, there is only **master**.

## Configuration pillar & variables
- We provide in **mc\_project** a powerfull mecanism to define configuration
  variables used in your deployments that you can safely override in the
  salt pillar files.<br/>
  This means that you can set some default values for,
  eg a domain name or a password, and input the production values that you
  won't commit along side your project codebase.
    - Default values have to be stored inside the **PILLAR.sample** file.
    - Some of those variables, the one at the first level are mostly read
      only and setup by makina-states itself.<br/>
      The most important are:
      - `name`: project name
      - `user`: the system user of your project
      - `group`: the system group of your project
      - `data`: top level free variables mapping
      - `project_root`: project root absolute path
      - `data_root`: persistent folder absolute path
      - `default_env`: environment (staging/prod/dev)
      - `pillar_root`: absolute path to the pillar
      - `fqdn`: machine FQDN
    - The only variables that you can edit at the first level are:
        - **remote\_less**: is this project using git remotes for triggering deployments
        - **default\_env**: environement (valid values are staging/dev/prod)
    - The other variables, members of the **data** sub entry are free for you to add/edit.
    - Anything defined in the pillar `pillar/init.sls` overloads what is in `project/.salt/PILLAR.sample`.

- You can get and consult the result of the configuration assemblage like
  this:

      ```sh
      bin/salt-call --retcode-passthrough mc_project.get_configuration <project_name>
      ```

- Remember that projects have a name, and the pillar key to configure
  and overload your project configuration is based on this key.

    - EG: If your project is name **foo**, you ll have to use
      **makina-projects.foo** in place of **makina-projects.example**.

### Example:
- in `project/.salt/PILLAR.sample`, you have:

```yaml
makina-projects.projectname:
  data:
    start_cmd: 'myprog'
```

- in `pillar/init.sls`, you have:

```yaml
makina-projects.foo:
   data:
     start_cmd: 'myprog2'
```

- In your states files, you can access the configuration via the magic `opts.ms_project` variable.
- In your modules or file templates, you can access the configuration via `salt['mc_project.get_configuration'(name)`.
- A tip for loading the configuration from a template is doing something like that:

```yaml
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
```

## SaltStack integration
- As you know makina-states embeds its own virtualenv and salt codebase.<br/>
  In makina-states, we use by default:
    - makina states itself: `/srv/makina-states`
    - a virtualenv inside `/srv/makina-states/venv`
    - [salt from a fork](https://github.com/makina-corpus/salt.git) installed inside `$makinastates/venv/src/salt`

- As you see, the project layout seems not integration on those following
  folders, but in fact, the project initialisation routines made symlinks
  to integrate it which look like:
    - `$makinastates/salt/makina-projects/<project_name>>` -> `/srv/projects/<project_name>/project§/.salt`
    - `$makinastates/pillar/pillar.d/makina-projects/<project_name>` -> `/srv/projects/<project_name>/pillar`

- The pillar is auto included in the **pillar top** (`/srv/pîllar/top.sls`).
- The project salt files are not and **must not** be included in the
  salt **top** for further highstates unless you know what you are doing.

- You can unlink your project from salt with:

   ```sh
   bin/salt-call --retcode-passthrough mc_project.unlink <project_name>
   ```

- You can link project from salt with:

   ```sh
   bin/salt-call --retcode-passthrough mc_project.link <project_name>
   ```

