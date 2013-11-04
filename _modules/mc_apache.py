'''
Management of Apache, Makina Corpus version
============================================

If you alter this module and want to test it, do not forget to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_apache

Check the mc_apache states for details. If you use this module as a template for a new module
do not forget to use salt-modules state in makina-states/servies/salt to get this module
included in salt modules (first time, this will build the symlinks linking the module
on /srv/salt/[_modules|_states, etc])::

  salt-call state.sls makina-states.services.salt
'''

# Import python libs
import logging


# Import salt libs
import salt.utils

log = logging.getLogger(__name__)

def check_version(version):
    '''
    Ensures the installed apache version matches all the given version number

    For a given 2.2 version 2.2.x current version would return an OK state

    version
        The apache version

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.check_version 2.4
    '''

    ret = {'result': None,
           'comment': ''}
    full_version = __salt__['apache.version']()
    # Apache/2.4.6 (Ubuntu) -> 2.4.6
    _version=full_version.split("/")[1].split(" ")[0]
    op_version_list = str(version).split(".") # [2][4]
    current_version_list = str(_version).split(".") #[2][4][6]
    for number1, number2 in zip(op_version_list,current_version_list):
        if not number1 is number2:
            ret['result'] = False
            ret['comment'] = 'Apache requested version {0} is not verified by current version: {1}'.format(_version,version)
            return ret
    ret['result'] = True
    ret['comment'] = 'Apache version {0} verify requested {1}'.format(_version,version)
    return ret

def a2enmod(module):
    '''
    Runs a2enmod for the given module.

    This will only be functional on Debian-based operating systems (Ubuntu,
    Mint, etc).

    module
        string, module name

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.a2enmod autoindex
    '''
    ret = {}
    command = ['a2enmod', module]

    try:
        status = __salt__['cmd.retcode'](command, python_shell=False)
    except Exception as e:
        return e

    ret['Name'] = 'Apache2 Enable Module'
    ret['Module'] = module
    ret['result'] = False

    if status == 1:
        ret['Status'] = 'Module {0} Not found'.format(module)
    elif status == 0:
        ret['Status'] = 'Module {0} enabled'.format(module)
        ret['result'] = True
    else:
        ret['Status'] = status

    return ret


def a2dismod(module):
    '''
    Runs a2dismod for the given module.

    This will only be functional on Debian-based operating systems (Ubuntu,
    Mint, etc).

    module
        string, module name

    CLI Examples:

    .. code-block:: bash

        salt '*' mc_apache.a2dismod autoindex
    '''
    ret = {}
    command = ['a2dismod', module]

    try:
        status = __salt__['cmd.retcode'](command, python_shell=False)
    except Exception as e:
        return e

    ret['Name'] = 'Apache2 Disable Modules'
    ret['Module'] = module
    ret['result'] = False

    if status == 1:
        ret['Status'] = 'Module {0} Not found'.format(module)
    elif status == 0:
        ret['Status'] = 'Module {0} disabled'.format(module)
        ret['result'] = True
    else:
        ret['Status'] = status

    return ret
