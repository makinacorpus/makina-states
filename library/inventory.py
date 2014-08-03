#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from mc_states.ansible.inventory import MakinaStatesInventory
inv = MakinaStatesInventory()
inv.to_stdout()
