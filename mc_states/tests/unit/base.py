#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import os
import copy
import re
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import salt.loader
from salt.utils.odict import OrderedDict
from contextlib import nested
import contextlib
import mc_states
import mc_states.tests
import mc_states.modules
import mc_states.modules.mc_utils
from mock import patch

A = os.path.abspath
J = os.path.join
D = os.path.dirname
sys.path.append(D(D(mc_states.__file__)))


import mc_states.tests.utils
import mc_states.saltapi
import mc_states.api

six = mc_states.saltapi.six

_NO_ATTR = object()
_KIND = 'modules'
re_cache = {}


class _ModuleCase(unittest.TestCase):
    '''Base test class
    Its main function is to be used in salt modules
    and to mock the __salt__, __pillar__ and __grains__ attributes
    all in one place

    '''
    maxDiff = None
    _context_mods = ('utils',
                     'search',
                     'engines',
                     'clouds',
                     'netapi',
                     'beacons',
                     'wheels',
                     'queues',
                     'tops',
                     'roster',
                     'grains',
                     'fileserver',
                     'renderers',
                     'auth',
                     'wrapper',
                     'log_handlers',
                     'proxy'
                     'sdb',
                     'context',
                     'dunders')
    kind = None
    contextual = ('opts', 'context', 'pillar', 'grains')

    def _(self, fun, *args, **kwargs):
        func = self.salt[fun]
        if args and kwargs:
            ret = func(*args, **kwargs)
        elif kwargs and not self.args:
            ret = func(**kwargs)
        elif args and not kwargs:
            ret = func(*args)
        else:
            ret = func
        return ret

    def reset(self):
        for i in [a for a in mc_states.api._LOCAL_CACHES]:
            mc_states.api._LOCAL_CACHES.pop(i, {})
        for i in [a for a in self.dunders_]:
            val = self.dunders_.pop(i)
            del val
        for i in ('dunders',) + self.contextual:
            k = i + '_'
            dval = getattr(self, '__{0}'.format(i), {})
            if isinstance(dval, dict):
                dval = copy.deepcopy(dval)
            setattr(self, k, dval)

    def __init__(self, *args, **kwargs):
        super(_ModuleCase, self).__init__(*args, **kwargs)
        self.states_dir = A(D(mc_states.__file__))
        self.ms = A(D(self.states_dir))
        self.salt_root = A(D(self.ms))
        self.root = '/'
        # adding an underscore for not having properties that
        # conflict with nose
        self.dunders_ = {}
        self.opts_ = {}
        self.context_ = {}
        self.pillar_ = {}
        self.grains_ = {}
        self.salt = {}
        self.reset()

    def get_opts(self):
        opts = {'root': self.root,
                'root_dir': self.root,
                'cachedir': '{root}/cache',
                'makina-states.localsettings.locations.root': self.root,
                'makina-states.localsettings.locations.root_dir': self.root,
                'testroot': '{root}',
                'ms_conf': '{root}/etc/makina-states',
                'mms_conf': '{root}/etc/salt/makina-states',
                'salt_ms_conf': '{root}/etc/salt/makina-states',
                'salt_root': self.salt_root,
                'config_dir': '{root}/etc/salt',
                'conf_file': '{config_dir}/minion',
                'providers': {},
                'default_include': 'minion.d',
                'grains': {},
                'pillar_roots': {'base': ['{testroot}/srv/pillar']},
                'file_roots': {'base': [self.salt_root]},
                'file_buffer_size': 4096,
                'extension_modules': '{testroot}/var/cache/salt',
                'renderer': 'yaml_jinja'}
        with open(J(self.states_dir, 'modules_dirs.json')) as fic:
            content = json.loads(fic.read())
            opts.update(content)
        opts = mc_states.modules.mc_utils.format_resolve(opts)
        if not os.path.exists(opts['cachedir']):
            os.makedirs(opts['cachedir'])
        return opts

    def __(self, fun, *args, **kwargs):
        '''
        Shortcut to call functions without args instead of returning obj
        '''
        ret = self._(fun, *args, **kwargs)
        if not args and not kwargs:
            ret = ret()
        return ret

    @property
    def copts(self):
        return copy.deepcopy(self.opts_)

    def setUp(self):
        '''
        1. Monkey patch the dunders (__salt__, __grains__ & __pillar__; etc)
        in the objects (certainly python modules) given in self.mods

            - This search in self._{grains, pillar, salt} for a dict containing
              the monkey patch replacement and defaults to {}
            - We will then have on the test class _salt, _grains & _pillar
              dicts to be used and mocked in tests, this ensure that the mock
              has to be done only at one place, on the class attribute.

        '''
        self.root = mc_states.tests.utils.test_setup()
        self.reset()
        if not self.kind:
            self.kind = _KIND
        self.opts_.update(self.get_opts())
        for i in ['config_dir',
                  'ms_conf',
                  'mms_conf',
                  'salt_ms_conf',
                  'pillar_roots',
                  'extension_modules']:
            d = self.opts_[i]
            if i in ['pillar_roots']:
                d = d['base'][0]
            if not os.path.exists(d):
                os.makedirs(d)
        if not os.path.exists(self.opts_['conf_file']):
            with open(self.opts_['conf_file'], 'w') as fic:
                fic.write('')
        self.grains_.update(salt.loader.grains(self.opts_))
        self.opts_['grains'] = self.grains_
        self.opts_['pillar'] = self.pillar_
        self.dunders_['grains'] = salt.loader.LazyLoader(
            salt.loader._module_dirs(
                self.opts_,
                'grains',
                'grain',
                ext_type_dirs='grains_dirs'),
            self.opts_,
            tag='grains')
        self.dunders_['utils'] = salt.loader.utils(self.opts_)
        self.dunders_['modules'] = salt.loader.minion_mods(
            self.opts_,
            context=self.context_,
            utils=self.dunders_['utils'])
        self.dunders_['roster'] = salt.loader.roster(self.opts_)
        self.dunders_['fileserver'] = salt.loader.fileserver(self.opts_, {})
        self.dunders_['auth'] = salt.loader.auth(self.opts_)
        self.dunders_['log_handlers'] = salt.loader.log_handlers(self.opts_)
        self.dunders_['outputters'] = salt.loader.outputters(self.opts_)
        self.dunders_['wheels'] = salt.loader.wheels(self.opts_)
        self.dunders_['wrapper'] = salt.loader.ssh_wrapper(
            self.opts_,
            functions=self.dunders_['modules'],
            context=self.context_)
        self.dunders_['tops'] = salt.loader.tops(self.opts_)
        self.dunders_['runners'] = salt.loader.runner(self.opts_)
        self.dunders_['engines'] = salt.loader.engines(
            self.opts_, self.dunders_['modules'], self.dunders_['runners'])
        self.dunders_['proxy'] = salt.loader.proxy(
            self.opts_, self.dunders_['modules'])
        self.dunders_['returners'] = salt.loader.returners(
            self.opts_, self.dunders_['modules'], context=self.context_)
        self.dunders_['states'] = salt.loader.states(
            self.opts_, self.dunders_['modules'])
        self.dunders_['beacons'] = salt.loader.beacons(
            self.opts_, self.dunders_['modules'], context=self.context_)
        self.dunders_['search'] = salt.loader.search(
            self.opts_, self.dunders_['returners'])
        self.dunders_['sdb'] = salt.loader.sdb(
            self.opts_, self.dunders_['modules'])
        self.dunders_['queues'] = salt.loader.queues(self.opts_)
        self.dunders_['clouds'] = salt.loader.clouds(self.opts_)
        self.dunders_['netapi'] = salt.loader.netapi(self.opts_)
        self.dunders_['renderers'] = salt.loader.render(
            self.opts_,
            self.dunders_['modules'],
            states=self.dunders_['states'])
        self.salt = self.dunders_[self.kind]

    def tearDown(self):
        '''
        1. Ungister any Monkey patch on  __salt__, __grains__ & __pillar__ in
        objects (certainly python modules) given in self.mods
        '''
        self.reset()
        mc_states.tests.utils.test_teardown()

    def patch(self, force_load=True, kinds=None, **kwargs):
        '''
        opts
            overriden opts
        context
            overriden context
        pillar
            overriden pillar
        grains
            overriden grains
        funcs
            override something in the dunders indexed by kind (modules,
            runners, etc)

        .. code-block:: python

            with self.patch(grains={1:2}, context={3: 4}):
                ret1 = self._('mc_remote.sls')()

        .. code-block:: python

            with self.patch(opts={1: 2}, pillar={'secret': 'secret'}):
                ret1 = self._('mc_remote.sls')()

        .. code-block:: python

            def _do(*args, **kw):
                return {}

            with self.patch(funcs={
                'modules': {'mc_remote.salt_call': Mock(side_effect=_do)},
                'pillars': {'mc_remote.salt_call': Mock(side_effect=_do)}
            }):
                ret1 = self._('mc_remote.sls')()

        '''
        tpatchs = OrderedDict()
        globs = kwargs.get('globs', {})
        mod_globs = {}
        funcs = kwargs.get('funcs', {})
        for module, funcsdata in funcs.items():
            for fun, callback in funcsdata.items():
                if '.' in fun:
                    module, sfun = fun.split('.')
                    mglobs = mod_globs.setdefault(module, copy.deepcopy(globs))
                    mglobs[sfun] = callback
                    k = 'patch_fun_{0}{1}'.format(module, fun)
                    tpatchs[k] = patch.dict(self.salt, {fun: callback})
        for opt in self.contextual:
            overriden = kwargs.get(opt, {})
            tpatchs[opt] = patch.dict(getattr(self, opt+'_'), overriden)
        if not kinds:
            kinds = [a for a in self.dunders_]
        for kind in kinds:
            mods = self.dunders_[kind]
            # force lazyloader to load all
            if force_load:
                mods = [a for a in self.dunders_[kind]]
            filtered = kwargs.get('filtered', None)
            if filtered is None:
                filtered = mods[:]
            if not filtered:
                continue
            for mod in mods:
                matched = False
                for match in filtered:
                    rmatch = re_cache.get(match)
                    if not rmatch:
                        rmatch = re_cache[match] = re.compile(match)
                    if rmatch.search(mod):
                        matched = True
                        break
                if not matched:
                    continue
                func = self.dunders_[kind][mod]
                if not isinstance(func, dict):
                    try:
                        _globals = func.__globals__
                    except AttributeError:
                        continue
                    thismod = mod.split('.')[0]
                    globspatch = mod_globs.setdefault(thismod, {})
                    for i in globs:
                        globspatch[i] = globs[i]
                    k = '{0}.{1}'.format(kind, mod)
                    for opt in self.contextual:
                        gopt = '__{0}__'.format(opt)
                        if gopt in _globals:
                            globspatch[gopt] = getattr(self, opt+'_')
                    tpatchs[k] = patch.dict(func.__globals__, globspatch)
        return contextlib.nested(*tuple(tpatchs.values()))

    def get_private(self, private_name, public_name=None, kind=None):
        '''
        Hackery to load a private function from a LazyLoaded module

        public_name can be given for performances reasons (not to load the full
        loader)
        '''
        if '.' not in private_name:
            raise ValueError('need a module')
        mod, sfun = private_name.split('.', 1)
        if not kind:
            kind = self.kind
        func = None
        if public_name:
            try:
                func = self.dunders_[kind][
                    public_name].__globals__[sfun]
            except (KeyError, AttributeError):
                pass
        if func is None:
            for fname, f_ in six.iteritems(self.dunders_[kind]):
                if fname.startswith(mod+'.'):
                    try:
                        func = f_.__globals__[sfun]
                        break
                    except (KeyError, AttributeError):
                        continue
        if func is None:
            raise ValueError('cant find a public function to load '
                             '{0}'.format(private_name))
        return func


class GrainsCase(_ModuleCase):
    kind = 'grains'


class ModuleCase(_ModuleCase):
    kind = 'modules'


class RunnerCase(_ModuleCase):
    kind = 'runners'
# vim:set et sts=4 ts=4 tw=80:
