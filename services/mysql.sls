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
 
