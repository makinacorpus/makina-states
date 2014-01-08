# -*- coding: utf-8 -*-
{% from 'makina-states/services/db/mysql.sls' import mysql_base,mysql_db with context %}
{# Install MySQL on this server #}
{{  mysql_base() }}
{# Create a database foobar, accessed by user foo_user with password foo #}
{{ mysql_db(
    db='foobar',
    user='foouser',
    password='foo',
    state_uid='exampletest') }}
{# Create a database foobar2, accessed by user foobar2 with password foo from 3 IPs #}
{{ mysql_db(
    db='foobar2',
    host = ['127.0.0.1','10.0.0.1','10.0.0.2'],
    password='foo',
    state_uid='exampletest2') }}

{#Remove things created on theses examples #}
{% from 'makina-states/services/db/mysql_defaults.jinja' import mysqlData with context %}
makina-mysql-example-cleanup-db-foobar:
  mysql_database.absent:
    - name: foobar
    - connection_charset: "{{ mysqlData.character_set }}"
    - connection_host: "{{ mysqlData.conn_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
  mysql_user.absent:
    - name: foouser
    - host: '%'
    - connection_charset: "{{ mysqlData.character_set }}"
    - connection_host: "{{ mysqlData.conn_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"

makina-mysql-example-cleanup-db-foobar2:
  mysql_database.absent:
    - name: foobar2
    - connection_charset: "{{ mysqlData.character_set }}"
    - connection_host: "{{ mysqlData.conn_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
  mysql_user.absent:
    - name: foobar2
    - host: '127.0.0.1'
    - connection_charset: "{{ mysqlData.character_set }}"
    - connection_host: "{{ mysqlData.conn_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"

makina-mysql-example-cleanup-db-foobar2-bis:
  mysql_user.absent:
    - name: foobar2
    - host: '10.0.0.1'
    - connection_charset: "{{ mysqlData.character_set }}"
    - connection_host: "{{ mysqlData.conn_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"

makina-mysql-example-cleanup-db-foobar2-ter:
  mysql_user.absent:
    - name: foobar2
    - host: '10.0.0.2'
    - connection_charset: "{{ mysqlData.character_set }}"
    - connection_host: "{{ mysqlData.conn_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
