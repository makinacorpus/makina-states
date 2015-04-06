rc.local managment
====================
manage /etc/rc.local via helper scripts in **/etc/rc.local.d**
goal is to launch tricky services on the end of init processes.
Eg launch the firewall only after lxc interfaces are up and so on.

Idea is that you just have to drop executable files inside /etc/rc.local.d and
they will be executed (lexicographical order) at boot.



