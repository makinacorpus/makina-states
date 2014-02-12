Installing a project on a production environment
================================================
- At makina corpus where the states tree resides in a salt branch of our projects, we can use this script to deploy a project from salt to the project itself.
- For this, prior to execute the script, you can tell which project url, name, and branch to use.
- See also https://github.com/makinacorpus/salt-project
- You can safely use the script multiple times to install projects (even long first after installation)
- In most case, if the script has run once, you can relaunch it and it may have enought information on the system
  to guess how to run itself, just verify the variables sum up at the beginning.

::

    mkdir /srv/pillar
    # $ED is your default editor, rplace with nano, vim or anything
    # if the default is not the one you want
    $ED /srv/pillar/top.sls
    $ED /srv/pillar/foo.sls
    export NAME="foo" (default: no name)
    export URL"GIT_URL" (default: no url)
    export BRANCH="master" (default: salt)
    export TOPSTATE="deploy.foo" (default: no default but test if top.sls exists and use it")
    boot-salt.sh --project-url $URL --project-branch $BRANCH --project-state $TOPSTATE

Optionnaly you can edit your pillar in **/srv/pillar**::

    $ED /srv/pillar/top.sls

Then run higtstate or any salt cmd::

    salt-call state.highstate

According to makinacorpus projects layouts, your project resides in:

    - **/srv/projects/$PROJECT_NAME**: root prefix
    - **/srv/projects/$PROJECT_NAME/salt**: the checkout of the salt branch
    - **/srv/projects/$PROJECT_NAME/project**:  should contain the main project code source and be initialised by your project top.sls
    - **/srv/salt/makina-projects/$PROJECT_NAME**: symlink to the salt branch

Example to install the most simple project::

    URL="https://github.com/makinacorpus/salt-project.git"  BRANCH="sample-salt" NAME="sample"
    boot-salt.sh --project-url $URL --project-branch $BRANCH

Mastersalt specific
-----------------------
If you runned the mastersalt install, tell an admin to accept the mastersalt-minion key on the MasterofMaster::

    mastersalt-key -A

you can then do any further needed configuration from mastersalt::

    mastersalt 'thisminion' state.show_highstate
    mastersalt 'thisminion' state.highstate

Or from local when admins have configured things::

    salt-call -c /etc/mastersalt  state.show_highstate
 
