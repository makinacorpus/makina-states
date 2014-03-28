 {% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.cloud.generic.hooks.generate
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{%  for vmname, data in vms.items() -%}
{% set cptslsnamepref = '{1}/{0}/lxc/{2}'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir,
                                           vmname.replace('.', '')) %}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, vmname)})%}
{%    do data.update({'target': target})%}
{% set sname = data.get('state_name', data['name']) %}
{% set vmname = data['name'] %}
{% set dnsservers = data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]) -%}
c{{sname}}-lxc.computenode.sls-generator-for-spawn:
  file.managed:
    - name: {{cloudSettings.root}}/{{cptslsnamepref}}/run-spawn.sls
    - user: root
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - mode: 750
    - makedirs: true
    - contents: |
        include:
          - makina-states.cloud.generic.hooks.vm
          - makina-states.cloud.lxc.controller.install
        {{sname}}-lxc-deploy:
          cloud.profile:
            - name: {{vmname}}
            {% set minion = {"master": data.master,
                              "master_port": data.master_port} %}
            {% set sminion = minion|yaml %}
            {% set sminion = sminion.replace('\n', ' ') %}
            {% set sdata = data|yaml %}
            {% set sdata = sdata.replace('\n', ' ') %}
            {% set sserver = dnsservers|yaml %}
            {% set sserver = sserver.replace('\n', ' ') %}
            {%raw%}{%set dnsservers="{%endraw%}{{sserver}}{%raw%}"|load_yaml%}{%endraw%}
            {%raw%}{%set data="{% endraw %}{{sdata}}{%raw%}"|load_yaml%}{% endraw %}
            {%raw%}{%set minion="{% endraw %}{{sminion}}{%raw%}"|load_yaml%}{% endraw %}
            - profile: {{data.get('profile', 'ms-{0}-dir-sratch'.format(data['target']))}}
            - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{vmname}}
            - watch:
              - mc_proxy: cloud-generic-vm-pre-deploy
            - watch_in:
              - mc_proxy: cloud-generic-vm-post-deploy
            - minion: {%raw%} {{ minion | yaml }} {%endraw%}
            - dnsservers: {%raw%}{{dnsservers|yaml}}{%endraw%}
            {% for var in ["from_container", "snapshot", "image",
                           "gateway", "bridge", "mac", "lxc_conf_unset",
                           "ssh_gateway", "ssh_gateway_user", "ssh_gateway_port",
                           "ssh_gateway_key", "ip", "netmask",
                           "size", "backing", "vgname",
                           "lvname", "script_args", "dnsserver",
                           "ssh_username", "password", "lxc_conf"] -%}
            {%- if data.get(var) %}{% set svar = data[var]|yaml %}{% set svar = svar.replace('\n', ' ') %}
            {# workaround for bizarious rendering bug with ' ...' at each variable end #}
            - {{var}}: {%raw%}{{"{% endraw %}{{salt['mc_utils.yencode'](svar)}}{% raw %}"|load_yaml}}{%endraw%}
            {%      endif -%}{% endfor %}
{%  endfor %}
{%  endif %}
{% endfor %}
