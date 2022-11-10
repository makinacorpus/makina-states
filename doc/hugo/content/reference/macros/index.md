---
title: Macros
tags: [reference, installation]
weight: 6000
menu:
  main:
    parent: reference
    identifier: reference_macros
---

Here are a non exhaustive list of macros that makina-states provides and you
may use in your states.

## Helpers
- [h(helpers)](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/_macros/h.jinja)


    - **deliver_deliver_config_files**: push  configuration files
	- **service_restart_reload**: aim to restart or reload service
      but handle the case where services mis implement the status
      function and mess salt modules.
	- **toggle_service**: helper to call **service_restart_reload**

## ssl
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/localsettings/ssl/macros.jinja)
    - install_certificate
    - install_cert_in_dir

## nginx
- [nginx](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/http/nginx/macros.sls)
    - [nginx.vhost](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/http/nginx/macros.sls#L31)


## apache
- [apache](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/http/apache/macros.sls)
    - [apache.vhost](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/http/apache/macros.sls#L48)

## php
- [php](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/php/macros.sls)
    - [php.fpm_pool](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/php/macros.sls#L60)
    - [php.minimal_index](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/php/macros.sls#L135)
    - [php.toggle_ext](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/php/macros.sls#L153)

## mysql
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/db/mysql/init.sls)
    - mysql_db
    - mysql_group

## postgresql
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/db/postgresql/init.sls)
    - postgresql_db
    - postgresql_user
    - postgresql_group
    - install_pg_exts
    - install_pg_ext

## circusd
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services_managers/circus/macros.jinja)
    - circusAddWatcher

## supervisord
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services_managers/supervisor/macros.jinja)
    - supervisorAddProgram

## mongodb
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/db/mongodb/macros.sls)
    - mongodb_db
    - mongodb_user

## uwsgi
- [macros](https://github.com/makinacorpus/makina-states/tree/v3/salt/makina-states/services/proxy/uwsgi)
    - config

## rabbitmq
- [macros](https://github.com/makinacorpus/makina-states/blob/v3/salt/makina-states/services/queue/rabbitmq/macros.sls)
    - rabbitmq_vhost

