import unittest
import mc_states.api

from . import base


class TestCase(base.ModuleCase):
    def test_is_valid_ip(self):
        self.assertTrue(mc_states.api.is_valid_ip("::1"))
        self.assertTrue(mc_states.api.is_valid_ip("1::1"))
        self.assertTrue(mc_states.api.is_valid_ip("1.2.3.4"))
        self.assertTrue(mc_states.api.is_valid_ip("255.255.255.255"))
        self.assertFalse(mc_states.api.is_valid_ip("255"))
        self.assertFalse(mc_states.api.is_valid_ip("a"))
        self.assertFalse(mc_states.api.is_valid_ip("www.foobar.com"))
