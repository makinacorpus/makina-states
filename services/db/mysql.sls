# define in pillar a mysql pillar entry:
#   mysql.passwd: 3l1t3

mysql-pkgs:
  pkg.installed:
    - names:
      - python-mysqldb
      - mysql-server

makina-mysql-service:
  service.running:
    - name: mysql
    - require:
      - pkg: mysql-pkgs
    - watch:
      - pkg: mysql-pkgs

# change password only if we can connect without
change-empty-mysql-root-access:
  cmd.run:
    - name: mysqladmin -u root password {{ pillar['mysql.pass'] }}
    - onlyif: echo "select 'connected'"|mysql -u root
    - require:
      - service: mysql

configure-minion-root-access:
  cmd.run:
    - name: mysqladmin -u root password {{ pillar['mysql.pass'] }}
    - onlyif: echo "select 'connected'"|mysql -u root
    - require:
      - service: mysql
 

{% import "openstack/config.sls" as config with context %}
{% set dconfig = config.__dict__ %}
mysql:
  service:
    - running
  require:
    - pkg.installed: mysql-server
  watch:
    - pkg.installed: mysql-server

{% for db in [
  'keystone',
  'horizon',
  'quantum',
  'glance',
  'cinder',
  'nova', 
  ] %}
{% for name, host in { 
  'localhost_ip':"127.0.0.1", 
  'localhost':"localhost", 
  'all':"'%'"}.items() %}
{% set d_k='mysql_'+db+'_database' %}
{% set p_k='mysql_'+db+'_password' %}
{% set u_k='mysql_'+db+'_username' %}
mysql-{{db}}-{{ name }}:
  mysql_database.present:
    - name: {{ dconfig[d_k] }}
  mysql_user.present:
    - name: {{ dconfig[u_k] }}
    - password: {{ dconfig[p_k] }}
    - host: {{ host }}
    - require:
      - mysql_database.present: mysql-{{db}}-{{ name }}
  mysql_grants.present:
    - grant: all
    - host: {{ host }}
    - user: {{ dconfig[u_k] }}
    - database: {{ dconfig[d_k] }}.*
    - require:
      - mysql_database.present: mysql-{{db}}-{{ name }}
  require:
    - service: mysql    
{% endfor %}
{% endfor %}
