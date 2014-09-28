#!/usr/bin/env bash
cd $(dirname $0)
W="$PWD"
su postgres -c "$W/check_postgres.pl $@"
