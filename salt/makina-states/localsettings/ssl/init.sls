{% import "makina-states/_macros/h.jinja" as h with context %}
{% import "makina-states/localsettings/ssl/macros.jinja" as ssl with context %}
{{ salt['mc_macros.register']('localsettings', 'ssl') }}
{% set settings = salt['mc_ssl.settings']() %}
{% set ssl = ssl %}
{% set install_certificate = ssl.install_certificate %}
{% set install_cert = ssl.install_cert %}
include:
  - makina-states.cloud.generic.hooks
  - makina-states.localsettings.ssl.hooks
  - makina-states.localsettings.pkgs.fixppas
makina-ssl-pkgs:
  pkg.latest:
    - pkgs: [ca-certificates, ssl-cert]
    - watch_in:
      - mc_proxy: ssl-certs-pre-install
      - mc_proxy: ssl-certs-post-install

makina-ssl-etc-cloud-user:
  group.present:
    - names: [{{settings.group}}]
    - system: true
    - watch:
      - mc_proxy: ssl-certs-post-install
    - watch_in:
      - mc_proxy: ssl-certs-pre-hook
  user.present:
    - name: {{settings.user}}
    - system: true
    - optional_groups: [{{settings.group}}]
    - remove_groups: false
    - watch:
      - group: makina-ssl-etc-cloud-user
      - mc_proxy: ssl-certs-post-install
    - watch_in:
      - mc_proxy: ssl-certs-pre-hook

makina-ssl-etc-cloud-cert-dirs:
  file.directory:
    - makedirs: true
    - mode: 751
    - user: {{settings.user}}
    - group: {{settings.group}}
    - names:
      - {{settings.config_dir}}
      - {{settings.config_dir}}/separate
      - {{settings.config_dir}}/trust
      - {{settings.config_dir}}/certs
    - watch:
      - user: makina-ssl-etc-cloud-user
      - mc_proxy: ssl-certs-post-install
    - watch_in:
      - mc_proxy: ssl-certs-pre-hook

{% macro rmacro() %}
    - watch:
      - mc_proxy: ssl-certs-pre-hook
    - watch_in:
      - mc_proxy: ssl-certs-clean-certs-pre
      - mc_proxy: ssl-certs-post-hook
{% endmacro %}
{{ h.deliver_config_files(settings.get('configs', {}),
                          mode='644',
                          after_macro=rmacro,
                          prefix='makina-ssl-certs-')}}

{# XXX: no way as it is used as a potential external macro
   to track in further calls exactly the certificates we need
   to manage, so we may remove certificates which are legitimate
makina-ssl-certs-cleanup:
  cmd.run:
    - name: {{settings.config_dir}}/cleanup_certs.py
    - stateful: true
    - watch:
      - mc_proxy: makina-ssl-certs-apply
    - watch_in:
      - cmd: makina-ssl-certs-trust
#}

makina-ssl-certs-trust:
  cmd.run:
    - name: {{settings.config_dir}}/trust.sh && echo "changed=no"
    - stateful: true
    - onlyif: test $(ls {{settings.config_dir}}/certs/*crt|wc -c) -gt 0
    - watch:
      - mc_proxy: ssl-certs-trust-certs-pre
    - watch_in:
      - mc_proxy: ssl-certs-trust-certs-post
      - mc_proxy: ssl-certs-post-hook

{% for cname, cdata in settings.cas.items() %}
{{ ssl.install_certificate(cdata[0], sinfos=cdata[2]) }}
{% endfor %}

{% for cname, cdata in settings.certificates.items() %}
{{ ssl.install_certificate(cname, sinfos=cdata[3])}}
{% endfor %}
