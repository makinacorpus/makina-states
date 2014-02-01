{#- Install in full mode, see the standalone file !  #}
{% import  "makina-states/services/mail/dovecot-standalone.sls" as base with context %}
{{base.do(full=True)}}

