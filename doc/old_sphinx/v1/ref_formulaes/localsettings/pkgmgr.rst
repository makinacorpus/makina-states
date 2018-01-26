Package manager configuration
===============================
Debian systems
------------------
Manage official apt mirrors, for thirdparty repositories, you may have better to write
a file in /etc/apt/sources.list.d/foo.list or better: use the salt pkgrepo.installed state.

Exposed settings:

    :makina-states.apt.ubuntu.mirror: debian mirror to use
    :makina-states.apt.debian.mirror: debian mirror to use
    :makina-states.apt.ubuntu.comps: main (defaults: main restricted universe multiverse) defaults comps to install on ubuntu
    :makina-states.apt.debian.comps: main (defaults: main contrib non-free) defaults comps to install on debian



