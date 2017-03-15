JDK configuration
=================

Oracle JDK configuration and installation on Debian like systems using
webupd8team  repos.

- It installs JDK6 & JDK7.
- It links the **jdkDefaultver** as default jdk

Exposed pillar settings
------------------------
    :makina-states.localsettings.java.default_jdk_ver: default jdk version (6 or 7)

Exposed hooks
-------------
    :makina-states-jdk_begin: before jdk install
    :makina-states-jdk_last: after jdk install


