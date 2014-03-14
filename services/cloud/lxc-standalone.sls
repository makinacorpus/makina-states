{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}


{% macro lxc_container(data) %}
{% set sname = data.get('state_name', data['name']) %}
{% set name = data['name'] %}
{% set dnsservers = data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]) -%}
{{sname}}-lxc-deploy:
  cloud.profile:
    - name: {{name}}
    - profile: {{data.get('profile', 'ms-{0}-dir-sratch'.format(data['target']))}}
    {% if name in ['makina-states'] %}
    - unless: test -e /var/lib/lxc/{{name}}/roots/etc/salt/pki/master/minions/makina-states
    {% else %}
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    {% endif %}
    - require:
      - mc_proxy: lxc-post-inst
      - mc_proxy: salt-cloud-predeploy
      - mc_proxy: salt-cloud-lxc-default-template
    - require_in:
      - mc_proxy: salt-cloud-postdeploy
      - mc_proxy: salt-cloud-lxc-devhost-hooks
    - minion: {master: "{{data.master}}",
               master_port: {{data.master_port}}}
    - dnsservers: {{dnsservers|yaml}}
{%    for var in ["from_container",
                   "snapshot",
                   "image",
                   "gateway",
                   "bridge",
                   "mac",
                   "ssh_gateway",
                   "ssh_gateway_user",
                   "ssh_gateway_port",
                   "ssh_gateway_key",
                   "ip",
                   "netmask",
                   "size",
                   "backing",
                   "vgname",
                   "lvname",
                   "script_args",
                   "dnsserver",
                   "ssh_username",
                   "password",
                   "lxc_conf",
                   "lxc_conf_unset"] %}
{%      if data.get(var) %}
    - {{var}}: {{data[var]}}
{%      endif%}
{%    endfor%}
{% endmacro %}

{% macro do(full=False) %}
{{- salt["mc_macros.register"]("services", "cloud.lxc") }}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.lxc-hooks
{% if full %}
  - makina-states.services.cloud.salt_cloud
{% else %}
  - makina-states.services.cloud.salt_cloud-standalone
{% endif %}
{% if nodetypes.registry.is.devhost %}
  - makina-states.services.cloud.lxc-devhost-sshkeys
{% endif %}


providers_lxc_salt:
  file.managed:
    - require:
      - mc_proxy: salt-cloud-preinstall
    - require_in:
      - mc_proxy: salt-cloud-postinstall
    - source: salt://makina-states/files/etc/salt/cloud.providers.d/makinastates_lxc.conf
    - name: {{pvdir}}/makinastates_lxc.conf
    - user: root
    - template: jinja
    - group: root
    - defaults:
        data: {{lxcSettings.defaults|yaml}}
        cdata: {{cloudSettings|yaml}}
        containers: {{lxcSettings.containers.keys()|yaml }}
        msr: {{saltmac.msr}}

profiles_lxc_salt:
  file.managed:
    - template: jinja
    - source: salt://makina-states/files/etc/salt/cloud.profiles.d/makinastates_lxc.conf
    - name: {{pfdir}}/makinastates_lxc.conf
    - user: root
    - group: root
    - defaults:
        pdata: {{lxcSettings.defaults|yaml}}
        cdata: {{cloudSettings|yaml}}
        profiles: {{lxcSettings.lxc_cloud_profiles|yaml }}
        containers: {{lxcSettings.containers.keys()|yaml }}
        msr: {{saltmac.msr}}
    - require:
      - mc_proxy: salt-cloud-preinstall
    - require_in:
      - mc_proxy: salt-cloud-postinstall

{% for name, imgdata in lxcSettings.images.items() %}
{% set cwd = '/var/lib/lxc/{0}'.format(name) %}
{% set arc = '{0}/{1}'.format(name, imgdata['lxc_tarball_name']) %}
{{grains.id}}-download-{{name}}:
  file.directory:
    - name: {{cwd}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 755
  archive.extracted:
    - name: {{cwd}}
    - source: {{imgdata.lxc_tarball}}
    - source_hash: md5={{imgdata.lxc_tarball_md5}}
    - archive_format: tar
    - if_missing: {{cwd}}/rootfs/etc/salt
    - tar_options: -xJf
    - require:
      - file: {{grains.id}}-download-{{name}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-restore-specialfiles-{{name}}:
  cmd.run:
    - name: cp -a /dev/log {{cwd}}/rootfs/dev/log
    - unless: test -e {{cwd}}/rootfs/dev/log
    - cwd: {{cwd}}
    - user: root
    - require:
      - archive: {{grains.id}}-download-{{name}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-restore-acls-{{name}}:
  cmd.run:
    - name: setfacl --restore=acls.txt && touch acls_done
    - cwd: {{cwd}}
    - unless: test -e {{cwd}}/acls_done
    - user: root
    - require:
      - cmd: {{grains.id}}-restore-specialfiles-{{name}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-stop-default-lxc-container:
  lxc.stopped:
    - name: {{name}}
    - require:
      - cmd: {{grains.id}}-restore-specialfiles-{{name}}
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-lxc-snap:
  cmd.run:
    - name: chroot /var/lib/lxc/{{name}}/rootfs/ /sbin/lxc-snap.sh
    - onlyif: test -e /var/lib/lxc/{{name}}/rootfs/etc/salt/pki/minion/minion.pub
    - require:
      - lxc: {{grains.id}}-{{name}}-stop-default-lxc-container
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template

{{grains.id}}-{{name}}-lxc-removeminion:
  file.absent:
    - name: {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    - require:
      - cmd: {{grains.id}}-{{name}}-lxc-snap
    - require_in:
      - mc_proxy: salt-cloud-lxc-default-template
{% endfor %}

{% if lxcSettings['cron_sync'] %}
syncron-lxc-ms:
  cron.present:
    - minute: {{lxcSettings.cron_minute}}
    - hour: {{lxcSettings.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser
{% endif %}

{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{{ lxc_container(data) }}
{%  endfor %}
{% endfor %}
{% endmacro %}
{{do(full=False)}}
