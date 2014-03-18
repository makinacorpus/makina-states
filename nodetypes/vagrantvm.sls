{# # Makina-states autodiscovery integration file #}
{% import "makina-states/nodetypes/vagrantvm-standalone.sls" as base with context %}
{{base.do(full=True)}}
{%- set vmNum = base.vmNum %}
{%- set vm_fqdn = base.vm_fqdn %}
{%- set vm_host = base.vm_host %}
{%- set vm_name = base.vm_name %}
{%- set vm_nat_fqdn = base.vm_nat_fqdn %}
{%- set ips = base.ips %}
{%- set ip1 = base.ip1 %}
{%- set ip2 = base.ip2 %}
{%- set hostsf = base.hostsf %}
