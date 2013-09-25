#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'


import docker

def get_client():
    """In a near future, use config to parameterize the url and cred"""
    client = docker.Client()
    return client

def get_containers():
    client = get_client()
    ret = client.containers(all=True, trunc=False)
    return ret

def stop(cid):
    client = get_client()
    client.stop(cid)

def restart(cid):
    client = get_client()
    client.restart(cid)

def start(cid):
    client = get_client()
    client.start(cid)

def kill(cid):
    client = get_client()
    client.kill(cid)
    
def wait(cid):
    client = get_client()
    client.wait(cid)

def login(url=None, name=None, password=None):
    c = __salt__['config.get']
    if not password:
        password = c('docker.registry.password')
    if not name:
        name = c('docker.registry.password')
    if not name:
        name = c('docker.registry.password')
    client = get_client()
    client.login(url, name, password)
 
def top(cid):
    client = get_client()
    client.top(cid)

def export(container):
    client = get_client()
    client.export(container)

def import_image(src, repo, tag=None):
    client = get_client()
    client.import_image(src, repo, tag=tag)

def get_images():
    client = get_client()
    client.images(all=True, trunc=False)

def build(path=None, tag=None, quiet=False, fileobj=None, nocache=False):
    client = get_client()
    client.build(path=path, tag=tag, quiet=quiet, 
                 fileobj=fileobj, nocache=nocache)

def remove_image(image):
    client = get_client()
    client.remove_image(image)

def remove_container(container):
    client = get_client()
    client.remove_container(container)

def inspect_image(image):
    client = get_client()
    client.inspect_image(image)

def inspect_container(container):
    client = get_client()
    client.inspect_container(container)

def port(repo, tag=None, registry=None):
    client = get_client()
    client.push(repo, tag, registry)

def push(repo, tag=None, registry=None):
    client = get_client()
    client.push(repo, tag, registry)

def pull(repo, tag=None, registry=None):
    client = get_client()
    client.pull(repo, tag, registry)

def install(
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
    containers = get_containers()
    import pdb;pdb.set_trace()  ## Breakpoint ##

# vim:set et sts=4 ts=4 tw=80:
