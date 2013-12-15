{% import "makina-states/_macros/salt.jinja" as c with context %}
{% set data = pillar.get('makina_ldap', {}) %}
{% set ldap_en = data.get('enabled', False) %}
{% set ntp_en = not c.lxc %}

#
# ntp is not applied to LXC containers !
# So we will just match when our grain is set and not have a value of lxc
#

include:
  - makina-states.localsettings.base
  - makina-states.services.base.ssh
  {% if ntp_en %}- makina-states.services.base.ntp{% endif %}
  {%- if ldap_en %}
  - makina-states.services.base.nscd
  - makina-states.services.base.ldap
  {% endif %}

# DONE MINION BY MINION, CANT BE GENERIC
#  - makina-states.services.firewall.shorewall
# TODO:
#  - makina-states.services.backups.bacula-fd
#  - makina-states.services.snmp
