#!/usr/bin/env bash
{% if __salt__ is defined %}
{% set ret=__salt__['saltutil.sync_grains']() %}
{% else %}
{% set ret=salt['saltutil.sync_grains']() %}
{% endif %}
echo "{{ret}}"
