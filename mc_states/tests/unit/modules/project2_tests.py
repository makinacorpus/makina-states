#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import unittest
import copy
from .. import base
import mock
from mc_states.api import six


SAMPLE = {
    "makina-projects.sample": {
        "data": {
            "has_guillestrois": False,
            "gtrois": {
                "xml_path": "{data_root}/gtrois",
                "ftp_host": "xxx",
                "ftp_user": "xxx",
                "ftp_pass": "xxx",
                "mail": 'sysadmin@{domain}',
                "periodicity": "* 6 * * *"
            },
            "has_services": True,
            "has_foobar": True,
            "domain": "{fqdn}",
            "db_name": "foobar",
            "db_host": '127.0.0.1',
            "db_port": 5432,
            "db_user": "foobar",
            "db_pass": "xxx",
            "psql_url":
            "postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
            "screamshotter_protocol": "http",
            "screamshotter_host": "0.0.0.0",
            "convertit_host": "0.0.0.0",
            "screamshotter_port": 8001,
            "convertit_protocol": "http",
            "convertit_port": 6543,
            "django_settings_source":
            "salt://makina-projects/{name}/files/config.py",
            "django_settings_module": "foobar.settings.custom",
            "htaccess": "/etc/nginx/{name}-access",
            "prepare_map_images_periodicity": "0 2 * * *",
            "prepare_elevation_charts_periodicity": "0 3 * * *",
            "path_trek_public_template": "",
            "path_touristiccontent_public_template": "",
            "path_touristicevent_public_template": {
                "path_logo_login":
                "salt://makina-projects/{name}/files/demo/logo-login.png",
                "path_logo_header":
                "salt://makina-projects/{name}/files/demo/logo-header.png"
            },
            "path_favicon":
            "salt://makina-projects/{name}/files/demo/favicon.png",
            "custom_fonts": ["demo/Yanone/YanoneKaffeesatz-Bold.ttf",
                             "demo/Yanone/YanoneKaffeesatz-Regular.ttf"],
            "users": [{"root": "root"}],
            "py": "{project_root}/bin/djangopy",
            "app_root": "{project_root}",
            "admins": [{"foo": {"mail": "a@a.com", "password": "xxx"}}],
            "DJANGO_SETTINGS_MODULE": "foobar.settings.custom",
            "USER_MODULE": "django.contrib.auth.models",
            "USER_CLASS": "User",
            "create_user": "{py} {project_root}/bin/django createsuperuser",
            "buildout": {
                "settings": {
                    "buildout": {
                        "newest": 'False',
                        "unzip": 'True',
                        "rotate": 365
                    },
                    "screamshotter": {
                        "protocol": "{screamshotter_protocol}",
                        "host": "{screamshotter_host}",
                        "port": "{screamshotter_port}"
                    },
                    "convertit": {
                        "protocol": "{convertit_protocol}",
                        "host": "{convertit_host}",
                        "port": "{convertit_port}"
                    },
                    "nginx-conf": {
                        "cache": "False",
                        "cachetime": "1d",
                        "server_name": "{domain}",
                        "cachename": "{name}one",
                        "level": "crit",
                        "default": "False",
                        "real_ip": "10.5.0.1",
                        "logformat": "custom_combined",
                        "server_aliases": ""
                    },
                    "versions": {
                        "Pillow": "2.5.0",
                        "pillow": "2.5.0"
                    },
                    "django": {
                        "settings": "settings.custom"
                    },
                    "settings": {
                        "defaultstructure": "PNX",
                        "language": "fr",
                        "languages": 'en,fr,it,es',
                        "dbname": '{db_name}',
                        "dbuser": '{db_user}',
                        "dbpassword": '{db_pass}',
                        "dbhost": '{db_host}',
                        "dbport": 5432,
                        "secret_key":
                        "change_this_key_with_a_value_of_your_choice",
                        "srid": 2154,
                        "spatial_extent": "924861,6375196,985649,6448688",
                        "wms_url": 'http"://{domain}/pnx/wms?',
                        "ortho_layers": "ortho",
                        "ortho_attributions": 'IGN BDOrtho',
                        "scan_layers": 'scan100,scan25',
                        "scan_attributions": 'IGN Scan',
                        "mailadmins": 'webmaster@{domain}',
                        "mailmanagers":
                        'webmaster@{domain}, sysadmin@{domain}',
                        "mailfrom": 'webmaster@{domain}',
                        "mailhost": '127.0.0.1',
                        "mailuser": '',
                        "mailpassword": '',
                        "mailport": 25,
                        "mailtls": 'False'
                    }
                }
            }
        }
    }
}
PILLAR = {
    'makina-projects.foobar': {
        'data': {
            "has_services": False,
            "has_foobar": True,
            "has_guillestrois": False,
            "django_settings_source":
            "salt://makina-projects/foobar/files/bbb/config.py",
            "admins": [{"tre": {"password": "hsxs",
                                "mail": "eee@makina-aaa.com"}},
                       {"aze": {"password": "uqezrf",
                                "mail": "fff@makina-bbb.com"}},
                       {"sysadmin": {"password": "azer",
                                     "mail": "ccc@ccc.com"}},
                       {"admin": {"password": "qazeraze",
                                  "mail": "admin@ccc.com"}}],
            "buildout": {
                "settings": {
                    "settings": {
                        "defaultstructure": "xx12",
                        "language": "fr",
                        "languages": "fr",
                        "secret_key": "{secret_key}",
                        "spatial_extent": "{spatial_extent}",
                        "mailadmins": "azerty@makina-aaa.com",
                        "mailmanagers": "cc@lcc.fr",
                        "experimental": True},
                    "nginx-conf": {"cors": "*"}
                }
            },
            "spatial_extent": "276225, 6639942, 404193, 6767911",
            "path_logo_header":
            "salt://makina-projects/foobar/files/xxx/logo.png",
            "path_trek_public_template":
            "salt://makina-projects/foobar/files/xxxx/trek_public.odt",
            "path_touristiccontent_public_template": (
                "salt://makina-projects/foobar/files/xxx"
                "/touristiccontent_public.odt"),
            "path_touristicevent_public_template":
            "salt://makina-projects/foobar/files/xxx/eee.odt",
            "domain": "foobar-bbb.ccc.net",
            "domains": ["foobar-bbb.ccc.net",
                        "lll-foobaryy-bo.ccc.net"],
            "server_aliases": ["zzz-geosze-bo.ccc.net"],
            "rando": {"cccc.cccc.net": ["rando.lccccique.fr",
                                        "randocccc.net",
                                        "lll-ccc.net"]},
            "rando_hosts": ["prcccc.ccc.net"],
            "rando_domains": ["rando.xxx.fr",
                              "rando-xxx.ccc.net",
                              "lll-foobarxxx.ccc.net"],
            "secret_key": "foobar012xx",
            "db_name": "foobar012xx",
            "db_user": "foobar012xx",
            "db_pass": "db_password",
            "db_password": "db_password",
            "db_host": "10.5.0.2",
            "convertit_host": "10.5.0.3",
            "screamshotter_host": "10.5.0.3"
        }
    }
}


class TestCase(base.ModuleCase):

    def test_get_configuration(self):
        func = self._('mc_project_2.get_configuration')

        def get_(*args, **kwargs):
            return copy.deepcopy(SAMPLE['makina-projects.sample']['data'])

        with self.patch(
            funcs={
                'modules': {
                    'mc_project_2.load_sample': get_,
                }
            },
            grains={},
            pillar=copy.deepcopy(PILLAR),
            filtered=['mc.*'],
            kinds=['modules']
        ):
            cfg = func('foobar')
            defaults = cfg['data']
            buildout = defaults['buildout']
            settings = buildout['settings']['settings']
            self.assertEqual(cfg['default_env'], 'dev')
            self.assertEqual(settings['secret_key'], 'foobar012xx')
            self.assertEqual(settings['dbpassword'], 'db_password')
            self.assertTrue(
                cfg['pillar_root'].endswith('/projects/foobar/pillar'))
            self.assertTrue(
                cfg['project_root'].endswith('/projects/foobar/project'))


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
