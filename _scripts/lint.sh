#!/usr/bin/env sh
cd $(dirname $0)
where=$PWD
s=$PWD/src/salt
"${where}/bin/pylint" --rcfile="$s/.testing.pylintrc" "$s/../../mc_states" "$s/salt" "$s/tests" && echo 'Finished Pylint Check Cleanly'
pylint="$?"
"${where}bin/pep8" --ignore=E501,E12 $s && echo 'Finished PEP-8 Check Cleanly'
pep8="$?"
ret="0"
if [ x"$pylint" != x"0" ];then
    echo 'Finished Pylint Check With Errors'
    ret="1"
fi
if [ x"$pep8" != x"0" ];then
     echo 'Finished PEP-8 Check With Errors'
    ret="2"
fi
exit $ret
