# -*- coding: utf-8 -*-
'''
YAML Renderer for Salt
'''


# Import python libs
import logging
import warnings
from yaml.scanner import ScannerError
from yaml.constructor import ConstructorError

# Import salt libs
from salt.utils.yamlloader import load
from salt.utils.odict import OrderedDict
from salt.exceptions import SaltRenderError
import salt.ext.six as six
from salt.ext.six import string_types
from salt.ext.six.moves import range
import yaml
from yaml.nodes import MappingNode
try:
    yaml.Loader = yaml.CLoader
    yaml.Dumper = yaml.CDumper
except Exception:
    pass


log = logging.getLogger(__name__)

_ERROR_MAP = {
    ("found character '\\t' that cannot "
     "start any token"): 'Illegal tab character'
}


class LYamlLoader(yaml.Loader, object):
    '''
    Create a custom YAML loader that uses the custom constructor. This allows
    for the YAML loading defaults to be manipulated based on needs within salt
    to make things like sls file more intuitive.
    '''
    def __init__(self, stream, dictclass=dict):
        yaml.Loader.__init__(self, stream)
        if dictclass is not dict:
            # then assume ordered dict and use it for both !map and !omap
            self.add_constructor(
                u'tag:yaml.org,2002:map',
                type(self).construct_yaml_map)
            self.add_constructor(
                u'tag:yaml.org,2002:omap',
                type(self).construct_yaml_map)
        self.dictclass = dictclass

    def construct_yaml_map(self, node):
        data = self.dictclass()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        '''
        Build the mapping for YAML
        '''
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None,
                None,
                'expected a mapping node, but found {0}'.format(node.id),
                node.start_mark)

        self.flatten_mapping(node)

        mapping = self.dictclass()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                err = ('While constructing a mapping {0} found unacceptable '
                       'key {1}').format(node.start_mark, key_node.start_mark)
                raise ConstructorError(err)
            value = self.construct_object(value_node, deep=deep)
            if key in mapping:
                raise ConstructorError('Conflicting ID {0!r}'.format(key))
            mapping[key] = value
        return mapping

    def construct_scalar(self, node):
        '''
        Verify integers and pass them in correctly is they are declared
        as octal
        '''
        if node.tag == 'tag:yaml.org,2002:int':
            if node.value == '0':
                pass
            elif (
                node.value.startswith('0')
                and not node.value.startswith(('0b', '0x'))
            ):
                node.value = node.value.lstrip('0')
                # If value was all zeros, node.value would have been reduced to
                # an empty string. Change it to '0'.
                if node.value == '':
                    node.value = '0'
        return super(LYamlLoader, self).construct_scalar(node)


def get_yaml_loader(argline, klass):
    '''
    Return the ordered dict yaml loader
    '''
    def yaml_loader(*args):
        return klass(*args, dictclass=OrderedDict)
    return yaml_loader


def render(yaml_data, saltenv='base', sls='', argline='', klass=None, **kws):
    '''
    Accepts YAML as a string or as a file object and runs it through the YAML
    parser.

    :rtype: A Python data structure
    '''
    if klass is None:
        klass = LYamlLoader
    if not isinstance(yaml_data, string_types):
        yaml_data = yaml_data.read()
    with warnings.catch_warnings(record=True) as warn_list:
        try:
            data = load(yaml_data,
                        Loader=get_yaml_loader(argline, klass=klass))
        except ScannerError as exc:
            err_type = _ERROR_MAP.get(exc.problem, 'Unknown yaml render error')
            line_num = exc.problem_mark.line + 1
            raise SaltRenderError(err_type, line_num, exc.problem_mark.buffer)
        except ConstructorError as exc:
            raise SaltRenderError(exc)
        if len(warn_list) > 0:
            for item in warn_list:
                log.warn(
                    '{warn} found in salt://{sls} environment={saltenv}'.format(
                        warn=item.message, sls=sls, saltenv=saltenv
                    )
                )
        if not data:
            data = {}
        else:
            if 'config.get' in __salt__:
                if __salt__['config.get']('yaml_utf8', False):
                    data = _yaml_result_unicode_to_utf8(data)
            elif __opts__.get('yaml_utf8'):
                data = _yaml_result_unicode_to_utf8(data)
        log.debug('Results of YAML rendering: \n{0}'.format(data))
        return data


def _yaml_result_unicode_to_utf8(data):
    ''''
    Replace `unicode` strings by utf-8 `str` in final yaml result

    This is a recursive function
    '''
    if isinstance(data, OrderedDict):
        for key, elt in six.iteritems(data):
            data[key] = _yaml_result_unicode_to_utf8(elt)
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = _yaml_result_unicode_to_utf8(data[i])
    elif isinstance(data, six.text_type):
        # here also
        data = data.encode('utf-8')
    return data
