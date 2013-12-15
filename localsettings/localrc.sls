#
# manage /etc/rc.local via helper scripts in /etc/rc.local.d
# goal is to launch tricky services on the end of init processes
#
# Eg launch the firewall only after lxc interfaces are up and so on
#

rc-local:
  file.directory:
    - name: /etc/rc.local.d
    - mode: 0755
    - user: root
    - group: root

rc-local-d:
  file.managed:
    - name: /etc/rc.local
    - source : salt://makina-states/files/etc/rc.local
    - mode: 0755
    - template: jinja
    - user: root
    - group: root
