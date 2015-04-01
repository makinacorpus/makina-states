{% set settings = salt['mc_slapd.settings']() %}
{% import "makina-states/localsettings/ssl/init.sls" as ssl with context %}
include:
  - makina-states.services.dns.slapd.hooks
  - makina-states.localsettings.ssl
cleanup-slapd-old-etc-ssl-cert:
  file.absent:
    - require_in:
      - mc_proxy: ssl-certs-pre-hook
    - names:
      - /usr/local/share/ca-certificates/{{settings.cert_domain}}.crt
      - /usr/local/share/ca-certificates/cacert{{settings.cert_domain}}.crt
{{ ssl.install_cert(settings.cert_domain, suf='ldap') }}
