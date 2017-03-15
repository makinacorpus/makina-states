---
title: LocalSettings
tags: [reference, installation]
weight: 4000
menu:
  main:
    parent: reference
---
- LocalSettings states are related to the low level configuration of an environment<br/>
  EG:
    - locales
    - network
    - low level configuration](hardrive, etc)
    - installing compilers & language interpreters
    - configuring base tools & editors
    - configuring SSH client
    - distributing SSL certificates

- If any other preset than ``scratch`` has been activated, <br/>
  Many localsettings will be applied by default, see [mc_localsettings:registry](https://github.com/makinacorpus/makina-states/blob/v2/mc_states/modules/mc_localsettings.py#L113)


## States
- [localsettings States](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings)
- non exhaustive shortcuts:

| State | State | State | State |
|-------|-------|-------|-------|
| [localsettings/apparmor](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/apparmor)         | [localsettings/nodejs](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/nodejs)                                | [localsettings/hostname](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/hostname)         | [localsettings/sudo](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/sudo)           |
| [localsettings/autoupgrade](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/autoupgrade)   | [localsettings/npm](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/npm)                                      | [localsettings/hosts](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/hosts)               | [localsettings/sysctl](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/sysctl)       |
| [localsettings/casperjs](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/casperjs)         | [localsettings/nscd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/nscd)                                    | [localsettings/init.sls](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/init.sls)         | [localsettings/systemd](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/systemd)     |
| [localsettings/check_raid](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/check_raid)     | [localsettings/phantomjs](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/phantomjs)                          | [localsettings/insserv](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/insserv)           | [localsettings/timezone](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/timezone)   |
| [localsettings/desktoptools](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/desktoptools) | [localsettings/pkgs](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/pkgs)                                    | [localsettings/jdk](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/jdk)                   | [localsettings/updatedb](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/updatedb)   |
| [localsettings/dns](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/dns)                   | [localsettings/python](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/python)                                | [localsettings/ldap](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/ldap)                 | [localsettings/users](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/users)         |
| [localsettings/editor](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/editor)             | [localsettings/reconfigure-network](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/reconfigure-network)      | [localsettings/locales](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/locales)           | [localsettings/vim](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/vim)             |
| [localsettings/env](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/env)                   | [localsettings/repository_dotdeb](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/repository_dotdeb)          | [localsettings/localrc](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/localrc)           | [localsettings/mvn](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/mvn)             |
| [localsettings/etckeeper](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/etckeeper)       | [localsettings/rvm](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/rvm)              | [localsettings/grub](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/grub)                 | [localsettings/ssl](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/ssl)             |
| [localsettings/git](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/git)                   | [localsettings/screen](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/screen)                                | [localsettings/golang](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/golang)             | [localsettings/shell](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/shell)         |
| [localsettings/groups](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/groups)             | [localsettings/sshkeys](https://github.com/makinacorpus/makina-states/tree/v2/salt/makina-states/localsettings/sshkeys)    |||

