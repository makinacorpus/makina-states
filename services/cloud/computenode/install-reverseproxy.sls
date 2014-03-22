{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.services.cloud.lxc.hooks
{# to reverse proxy a host, by default we redirect only and only:
 #  - http
 #  - https
 #  - ssh
 #
 # we can reverse proxy http & https but not ssh
 # for ssh, we are on a /16 by default (10.5/16)
 # so we have 256*254 maximum ports to redirect
 # We start by default at 40000
 # eg ip: 10.5.0.1 will have its ssh port mapped to 40001 on host
 # eg ip: 10.5.0.2 will have its ssh port mapped to 40002 on host
 # eg ip: 10.5.1.2 will have its ssh port mapped to 40258 on host
 #}
{% set localsettings = salt['mc_localsettings.settings']() %} %}
{% set nodetypes = services.nodetypes %}
{% for target, data in services.cloudcontrollerSettings['targets'].iteritems() %}
{% set cptslsname = 'cpt-nodes/{0}-reverseproxy'.format(target.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, saltmac.msaltRoot) %}
# get an haproxy proxying all request on 80+43 + alternate ports for ssh traffic
{% set sdata = data.haproxy|yaml %}
{% set sdata = sdata.replace('\n', ' ') %}
{{target}}-run-haproxy-installation:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
              include:
                - makina-states.services.proxy.haproxy
                - makina-states.services.firewall.shorewall
              cpt-cloud-target{{target}}-haproxy-cfg:
                file.managed:
                  - name: {{salt['mc_haproxy.settings']().config_dir}}/extra/cloudcontroller.cfg
                  - source: salt://makina-states/files/etc/haproxy/cloudcontroller.cfg
                  - user: root
                  - group: root
                  - mode: 644
                  - makedirs: true
                  - template: jinja
                  - defaults:
                    cdata: {{sdata}}
                  - watch:
                    - mc_proxy: haproxy-pre-conf-hook
                  - watch_in:
                    - mc_proxy: haproxy-post-conf-hook
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: {{target}}-run-haproxy-installation
      - mc_proxy: {{target}}-target-post-setup-hook
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
{% endfor %}
