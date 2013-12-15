#
# Salt base installation
# We set
#   - file_root: /srv/salt
#   - pillar_root: /srv/pillar
#   - conf: /etc/salt
#   - projects code source: /srv/projects
#   - sockets: /var/run/{master, minion}
#   - logs: /var/logs/salt/{master, minion}(key*)
#   - services: salt-minon & salt-master
#
# binaries:
#   - /usr/bin/salt
#   - /usr/bin/salt-key
#   - /usr/bin/salt-call
#   - /usr/bin/salt-master
#   - /usr/bin/salt-minion
#
# This state file only install a minion
#
# We create a group called editor which has rights in /srv/{pillar, salt, projects}
#
{% import "makina-states/_macros/salt.jinja" as c with context %}
{{ c.install_makina_states(c.saltname)}}
