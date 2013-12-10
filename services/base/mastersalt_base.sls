# As described in wiki each server has a local master
# but can also be controlled via the mastersalt
# We have the local master in /etc/salt
# and another dedicated to sysadmin called mastersalt::
#
#   - file_root: /srv/mastersalt
#   - pillar_root: /srv/mastersalt-pillar
#   - conf: /etc/mastersalt
#   - sockets: /var/run/mastersalt-*
#   - logs: /var/logs/salt/mastersalt-*
#   - services: mastersalt-minon & mastersalt-master
#
# binaries:
#   - /usr/bin/mastersalt
#   - /usr/bin/mastersalt-key
#   - /usr/bin/mastersalt-call
#   - /usr/bin/mastersalt-master
#   - /usr/bin/mastersalt-minion
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
#

{% import "makina-states/_macros/salt.jinja" as c with context %}
{{ c.install_makina_states(c.msaltname, mode='mastersalt')}}
