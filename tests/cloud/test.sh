#!/usr/bin/env bash
cd $(dirname $0)
salt-run -lall mc_cloud_controller.orchestrate only=[ovh-r4-1.makina-corpus.net] 2>&1
