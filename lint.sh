#!/usr/bin/env bash
cd $(dirname $0)
s=$PWD/src/salt
bin/pylint --rcfile="$s/.testing.pylintrc" "$s/salt" "$s/tests" && echo 'Finished Pylint Check Cleanly' 
if [[ "$?" != "0" ]];then
    echo 'Finished Pylint Check With Errors'
fi
bin/pep8 --ignore=E501,E12 $s && echo 'Finished PEP-8 Check Cleanly'
if [[ "$?" != "0" ]];then
     echo 'Finished PEP-8 Check With Errors'
fi

