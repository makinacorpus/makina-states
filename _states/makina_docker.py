'''
Management of dockers
==============================================

'''

def installed(
    name,
    url=None,
    image=None,
    docker_dir=None,
    hostname=None,
    branch=None,
    path=None,
    volumes=None,
    ports=None,
    *a, **kw):
    '''
    Configure a docker, see the .sls
    '''
    dc = __salt__['makina_docker']
    containers = dc.get_containers() 
    salt__.install_container(
    import pdb;pdb.set_trace()  ## Breakpoint ##
    ret = {'name':name,
           'changes':{},
           'result':None,
           'comment':'',}
    ret['comment'] += 'Updated bacula file daemon settings.\n'
    ret['result'] = True
    return ret
