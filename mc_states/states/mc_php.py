# -*- coding: utf-8 -*-
'''
mc_php / PHP tools
==================

This state can be used to make some fun things with PHP.
Like installing composer

.. code-block:: yaml

    install-global-php-composer:
      mc_php.composer:
        - name: /usr/local/bin/composer
        - installer: https://getcomposer.org/installer
        - update: False
'''

# Import python libs
import logging
import os

# Import salt libs
import salt.utils

log = logging.getLogger(__name__)


def _error(ret, err_msg):
    ret['result'] = False
    ret['comment'] = err_msg
    return ret

def composer(name,
           installer=None,
           update=False,
           
           ):
    '''
    Download composer.phar from the given url and install it on the given name.
    A check is done on the given name, if it's already available nothing is 
    done, except if update is set to True

    name
        Local file name of composer (like /usr/local/bin/composer)

    installer
        Distant name of composer phar installer source
        like https://getcomposer.org/installer which is the default

    update
        Boolean, whether to redo the install even if the program is already
        there or not.

    '''
    ret = {'name': name, 'result': True, 'comment': '', 'changes': {}}

    if not installer:
        installer = 'https://getcomposer.org/installer'

    if not os.path.isabs(name):
        return _error(ret,
                 'Specified file {0} is not an absolute path'.format(name))
    if os.path.exists(name) and not update:
        ret['message'] = '{0}: already installed. nothing to do'.format(name)
        return ret

    modres = __salt__['mc_php.composer'](name,
                                       installer,
                                       dry_run=__opts__['test'])

    ret['result'] = modres['status']
    ret['comment'] = modres['msg']

    return ret
