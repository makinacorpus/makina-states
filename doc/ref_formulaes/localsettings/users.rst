System Users & SSH accces configuration
=======================================
See also ssh service documentation

Basic configuration to create users based on pillar configuration.

The following states use those data mappings:

    - makina-states.localsettings.vim
    - makina-states.localsettings.users
    - makina-states.localsettings.git
    - makina-states.service.base.ssh


Pass generation
---------------
::

    >>> import crypt;print crypt.crypt('secret', '$6$SALTsalt$')

SSH
-----
To allow users to connect as root we define in pillar an entry which
ties #  ssh keys container in the 'keys' mapping to the near by
'users' mapping.
See makina-states.services.base.ssh.
::

    makina-states.localsettings.users.toto: []
    makina-states.localsettings.users.root:
        home: /users/root (opt)
        admin: true (opt)
        ssh_keys: ['kiorky.pub', 'salt://foo.pub']

- salt://files/ssh/kiorky.pub && salt://foo.pub will be authorized in root's authorized ssh keys
- This will also create root as an admin if not existing
- This will also create a standard user named 'toto'
- As you guessed, if you do not specify an url, the keys are looked in salt://files/ssh.

It will uses the **makina-states.localsettings.users** state registry configuration items.

Other settings:

    makina-states.localsettings.admin.sudoers
        sudoers list
    makina-states.localsettings.admin.sysadmins_keys
        ssh keyfiles to drop from saltmaster
    makina-states.localsettings.admin.sysadmin_password
        global sysadmin password hash
    makina-states.localsettings.admin.root_password
        root password hash (default to sysadmin if unset
    makina-states.localsettings.admin.absent_ssh_keys
        ssh keyfiles mappings to disable from auth (all users)

::

    makina-states.localsettings.admin.sudoers: [joe]
    makina-states.localsettings.admin.password: s3cret
    makina-states.localsettings.admin.absent_ssh_keys:
        AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr: {}
        AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr:
            enc: ssh-rsa
    makina-states.localsettings.admin.sysadmin_keys:
        - foo.pub
        - salt://foofoo.pub

If no root or sysadmin  password, no changes to the system
You have also a macro providen in this state to easily create users.


