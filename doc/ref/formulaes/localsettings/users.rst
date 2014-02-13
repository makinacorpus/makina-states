System Users & SSH accces configuration
=======================================
See also ssh service documentation

Basic configuration to create users based on pillar configuration.

For system users, we use special pillar entries suffixed by '-makina-users'
In those entries, we define a sub mapping with the key 'users' containing the users infos

The following states use those data mappings:

    - makina-states.localsettings.vim
    - makina-states.localsettings.users
    - makina-states.localsettings.git
    - makina-states.service.base.ssh

SSH
-----
To allow users to connect as root we define in pillar an entry which
ties #  ssh keys container in the 'keys' mapping to the near by
'users' mapping.
See makina-states.services.base.ssh.

foo-makina-users:
  keys:
    mpa:
      - kiorky.pub
  users:
    root:
      admin: True

bar-makina-users:
  toto: {}

====>

{
'ssh': {'root': {'mpa': ['kiorky.pub']}},
'users': {'root': {'admin': 'True'}, 'toto': {}}
}

- This allows mpa to connect as root which is a super user
- kiorky.pub will be authorized in root's authorized ssh keys
- This will also create root as an admin if not existing
- This will also create a standard user named 'toto'

It will uses the **makina-states.localsettings.users** state registry configuration items (all the makina-states.localsettings.users items) as the users where are dropped the ssh config slugs.
