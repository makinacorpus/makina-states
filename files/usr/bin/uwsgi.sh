#!/usr/bin/env bash
{% set data = salt['mc_uwsgi.settings']() %}
exec uwsgi --master --die-on-term --emperor {{data.configuration_directory}}/apps-enabled
# vim:set et sts=4 ts=4 tw=80:
