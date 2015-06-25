
# -*- coding: utf-8 -*-
'''
.. _module_mc_updatedb:

mc_updatedb / updatedb functions
==================================



'''

# Import python libs
import logging
import os
import mc_states.api
from salt.utils.pycrypto import secure_password


__name = 'updatedb'

log = logging.getLogger(__name__)


def settings():
    '''
    updatedb settings
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        salt = __salt__
        grains = __grains__
        pillar = __pillar__
        locs = __salt__['mc_locations.settings']()
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.updatedb', {
                "PRUNE_BIND_MOUNTS": "yes",
                "PRUNEPATHS": "/tmp /var/spool /media /home/.ecryptfs /srv /data",
                "PRUNEFS": ("NFS nfs nfs4 rpc_pipefs afs binfmt_misc proc "
                            "smbfs autofs iso9660 ncpfs coda devpts ftpfs "
                            " devfs mfs shfs sysfs cifs lustre tmpfs usbfs "
                            " udf fuse.glusterfs fuse.sshfs curlftpfs ecryptfs "
                            " fusesmb devtmpfs"),
        })
        return data
    return _settings()



#
