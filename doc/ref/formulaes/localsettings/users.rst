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
        ssh_keys: ['kiorky.pub']

- kiorky.pub will be authorized in root's authorized ssh keys
- This will also create root as an admin if not existing
- This will also create a standard user named 'toto'

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

If no root or sysadmin  password, no changes to the system

You have also a macro providen in this state to easily creae users.
