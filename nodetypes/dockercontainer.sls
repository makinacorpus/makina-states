{#
# Flag this machine as a docker container
# see:
#   - makina-states/doc/ref/formulaes/nodetypes/dockercontainer.rst
#}
{% import "makina-states/nodetypes/dockercontainer-standalone.sls" as base with context %}
{{base.do(full=True)}}
