{% import "makina-states/_macros/vars.jinja" as c with context %}

{% set shorewall_suf='' %}
{% if c.shorewall_enabled %}
{% set shorewall_suf='-shorewall' %}
{% endif %}

#
# ATTENTION:
# - SALT/MASTERSALT is part of the lowlevel tree infra, so we
#   install in the server part
# - Virt is for Hosts and not for container/guests, see servers.*containers for guests
#

include:
  - makina-states.localsettings.base
  - makina-states.services.base.ssh
  {% if c.ntp_en %}- makina-states.services.base.ntp{% endif %}
  {%- if c.ldap_en %}
  - makina-states.services.base.nscd
  - makina-states.services.base.ldap
  {% endif %}
  {% if c.shorewall_enabled and not c.docker_host and not c.lxc_host
  %}- makina-states.services.firewall.shorewall {% endif %}
  {% if c.docker_host %}- makina-states.services.virt.docker{{shorewall_suf}}{% endif %}
  {% if c.lxc_host %}- makina-states.services.virt.lxc{{shorewall_suf}}{% endif %}

# DONE MINION BY MINION, CANT BE GENERIC
#  - makina-states.services.firewall.shorewall
# TODO:
#  - makina-states.services.backups.bacula-fd
#  - makina-states.services.snmp
