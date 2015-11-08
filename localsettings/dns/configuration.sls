{% import "makina-states/localsettings/dns/macros.sls" as dns with context%}
{{ dns.switch_dns(suf='localsettings') }}
