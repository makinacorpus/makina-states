{% import "makina-states/services/firewall/firewall/init.sls" as f with context %}
{{f.fw(install=False)}}
