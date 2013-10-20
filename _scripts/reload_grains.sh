#!/usr/bin/env bash
{% set ret=__salt__['saltutil.sync_grains']() %}
echo "{{ret}}"
