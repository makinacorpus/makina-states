#!/usr/bin/env bash
cd $(dirname $0)
mastersalt-run -lall mc_cloud_controller.orchestrate only=[online-dc3-3.makina-corpus.net] 2>&1
