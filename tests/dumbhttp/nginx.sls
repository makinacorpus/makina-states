{% import "makina-states/services/http/nginx/init.sls" as nginx %}
include:
  - makina-states.services.http.nginx
{{ nginx.virtualhost(
  domain='www.testbottle.local',
  doc_root='/srv/',
  server_aliases=[],
  vhost_basename='makinastatesbottle',
  loglevel='crit',
  vh_content_source='salt://makina-states/tests/dumbhttp/nginx.conf',
  bport=4343)}}
