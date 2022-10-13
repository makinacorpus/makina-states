#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from salt.utils import fopen
except ImportError:
    from salt.utils.files import fopen

try:
    from salt.utils import traverse_dict
except ImportError:
    from salt.utils.data import traverse_dict

try:
    from salt.utils import check_state_result
    check_result = check_state_result
except ImportError:
    from salt.utils.state import check_result
    check_state_result = check_result

try:
    from salt.utils import clean_kwargs
except ImportError:
    from salt.utils.args import clean_kwargs

try:
    from salt.utils import get_colors
except ImportError:
    from salt.utils.color import get_colors

try:
    from salt.utils import DEFAULT_TARGET_DELIM
except ImportError:
    from salt.defaults import DEFAULT_TARGET_DELIM

# vim:set et sts=4 ts=4 tw=80:
