# -*- coding: utf-8 -*-
'''
Some usefull small tools
============================================

'''

# Import salt libs
import salt.utils
import salt.utils.dictupdate
from salt.exceptions import SaltException

def dictupdate( dict1, dict2 ):
    '''
      Merge two dictionnaries recursively
    
      test::
    
        salt '*' mc_utils.dictupdate '{foobar: {toto: tata, toto2: tata2},titi: tutu}' '{bar: toto, foobar: {toto2: arg, toto3: arg2}}'
        ----------
        bar:
            toto
        foobar:
            ----------
            toto:
                tata
            toto2:
                arg
            toto3:
                arg2
        titi:
            tutu
    '''
    if not isinstance(dict1, dict):
            raise SaltException('mc_utils.dictupdate 1st argument is not a dictionnary!')
    if not isinstance(dict2, dict):
            raise SaltException('mc_utils.dictupdate 2nd argument is not a dictionnary!')
    return salt.utils.dictupdate.update(dict1, dict2)
