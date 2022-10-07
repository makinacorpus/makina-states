#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_ssl:

mc_ssl / ssl registry
============================================



If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ssl

'''
# Import python libs
import logging
# Import salt libs
import traceback
import sys
from copy import deepcopy
import os
from salt.utils.odict import OrderedDict
import mc_states.api
import OpenSSL
from OpenSSL._util import lib as cryptolib
from urllib3.contrib.pyopenssl import get_subj_alt_name
import subprocess

"""
BACKPORT FROM PYOPENSSL 0.16
"""
from functools import partial
from six import (
    integer_types as _integer_types,
    text_type as _text_type,
    PY3 as _PY3)
from OpenSSL._util import (
    ffi as _ffi,
    lib as _lib,
    exception_from_error_queue as _exception_from_error_queue,
    byte_string as _byte_string,
    UNSPECIFIED as _UNSPECIFIED,
    text_to_bytes_and_warn as _text_to_bytes_and_warn,
)
FILETYPE_PEM = _lib.SSL_FILETYPE_PEM
FILETYPE_ASN1 = _lib.SSL_FILETYPE_ASN1
TYPE_RSA = _lib.EVP_PKEY_RSA
TYPE_DSA = _lib.EVP_PKEY_DSA

_raise_current_error = partial(
    _exception_from_error_queue, OpenSSL.crypto.Error)


def _new_mem_buf(buffer=None):
    """
    Allocate a new OpenSSL memory BIO.
    Arrange for the garbage collector to clean it up automatically.
    :param buffer: None or some bytes to use to put into the BIO so that they
        can be read out.
    """
    if buffer is None:
        bio = _lib.BIO_new(_lib.BIO_s_mem())
        free = _lib.BIO_free
    else:
        data = _ffi.new("char[]", buffer)
        bio = _lib.BIO_new_mem_buf(data, len(buffer))

        # Keep the memory alive as long as the bio is alive!
        def free(bio, ref=data):
            return _lib.BIO_free(bio)

    if bio == _ffi.NULL:
        # TODO: This is untested.
        _raise_current_error()

    bio = _ffi.gc(bio, free)
    return bio

class PKey(object):
    """
    A class representing an DSA or RSA public key or key pair.
    """
    _only_public = False
    _initialized = True

    def __init__(self):
        pkey = _lib.EVP_PKEY_new()
        self._pkey = _ffi.gc(pkey, _lib.EVP_PKEY_free)
        self._initialized = False

    def generate_key(self, type, bits):
        """
        Generate a key pair of the given type, with the given number of bits.
        This generates a key "into" the this object.
        :param type: The key type.
        :type type: :py:data:`TYPE_RSA` or :py:data:`TYPE_DSA`
        :param bits: The number of bits.
        :type bits: :py:data:`int` ``>= 0``
        :raises TypeError: If :py:data:`type` or :py:data:`bits` isn't\
                           of the appropriate type.
        :raises ValueError: If the number of bits isn't an integer of\
                            the appropriate size.
        :return: :py:const:`None`
        """
        if not isinstance(type, int):
            raise TypeError("type must be an integer")

        if not isinstance(bits, int):
            raise TypeError("bits must be an integer")

        # TODO Check error return
        exponent = _lib.BN_new()
        exponent = _ffi.gc(exponent, _lib.BN_free)
        _lib.BN_set_word(exponent, _lib.RSA_F4)

        if type == TYPE_RSA:
            if bits <= 0:
                raise ValueError("Invalid number of bits")

            rsa = _lib.RSA_new()

            result = _lib.RSA_generate_key_ex(rsa, bits, exponent, _ffi.NULL)
            if result == 0:
                # TODO: The test for this case is commented out.  Different
                # builds of OpenSSL appear to have different failure modes that
                # make it hard to test.  Visual inspection of the OpenSSL
                # source reveals that a return value of 0 signals an error.
                # Manual testing on a particular build of OpenSSL suggests that
                # this is probably the appropriate way to handle those errors.
                _raise_current_error()

            result = _lib.EVP_PKEY_assign_RSA(self._pkey, rsa)
            if not result:
                # TODO: It appears as though this can fail if an engine is in
                # use which does not support RSA.
                _raise_current_error()

        elif type == TYPE_DSA:
            dsa = _lib.DSA_new()
            if dsa == _ffi.NULL:
                # TODO: This is untested.
                _raise_current_error()

            dsa = _ffi.gc(dsa, _lib.DSA_free)
            res = _lib.DSA_generate_parameters_ex(
                dsa, bits, _ffi.NULL, 0, _ffi.NULL, _ffi.NULL, _ffi.NULL
            )
            if not res == 1:
                # TODO: This is untested.
                _raise_current_error()
            if not _lib.DSA_generate_key(dsa):
                # TODO: This is untested.
                _raise_current_error()
            if not _lib.EVP_PKEY_set1_DSA(self._pkey, dsa):
                # TODO: This is untested.
                _raise_current_error()
        else:
            raise Error("No such key type")

        self._initialized = True

    def check(self):
        """
        Check the consistency of an RSA private key.
        This is the Python equivalent of OpenSSL's ``RSA_check_key``.
        :return: True if key is consistent.
        :raise Error: if the key is inconsistent.
        :raise TypeError: if the key is of a type which cannot be checked.\
                          Only RSA keys can currently be checked.
        """
        if self._only_public:
            raise TypeError("public key only")

        if _lib.EVP_PKEY_type(self.type()) != _lib.EVP_PKEY_RSA:
            raise TypeError("key type unsupported")

        rsa = _lib.EVP_PKEY_get1_RSA(self._pkey)
        rsa = _ffi.gc(rsa, _lib.RSA_free)
        result = _lib.RSA_check_key(rsa)
        if result:
            return True
        _raise_current_error()

    def type(self):
        """
        Returns the type of the key
        :return: The type of the key.
        """
        return _lib.Cryptography_EVP_PKEY_id(self._pkey)

    def bits(self):
        """
        Returns the number of bits of the key
        :return: The number of bits of the key.
        """
        return _lib.EVP_PKEY_bits(self._pkey)

def load_publickey(type, buffer):
    """
    Load a public key from a buffer.
    :param type: The file type (one of :data:`FILETYPE_PEM`,\
                 :data:`FILETYPE_ASN1`).
    :param buffer: The buffer the key is stored in.
    :type buffer: A Python string object, either unicode or bytestring.
    :return: The PKey object.
    :rtype: :class:`PKey`

    COPIED AS IS FROM PYOPENSSL (because <0.16 does not have the method)

    """
    if isinstance(buffer, _text_type):
        buffer = buffer.encode("ascii")

    bio = _new_mem_buf(buffer)

    if type == FILETYPE_PEM:
        evp_pkey = _lib.PEM_read_bio_PUBKEY(
            bio, _ffi.NULL, _ffi.NULL, _ffi.NULL)
    elif type == FILETYPE_ASN1:
        evp_pkey = _lib.d2i_PUBKEY_bio(bio, _ffi.NULL)
    else:
        raise ValueError("type argument must be FILETYPE_PEM or FILETYPE_ASN1")

    if evp_pkey == _ffi.NULL:
        _raise_current_error()

    pkey = PKey.__new__(PKey)
    pkey._pkey = _ffi.gc(evp_pkey, _lib.EVP_PKEY_free)
    return pkey


"""
END PYOPENSSL BACKPORT
"""

HAS_SSL = True  # retrocompat
__name = 'ssl'
log = logging.getLogger(__name__)
PREFIX = 'makina-states.localsettings.ssl'


class CertificateNotFoundError(Exception):
    pass


class CertificateFileNotFoundError(CertificateNotFoundError):
    pass


class CertificateKeyFileNotFoundError(CertificateFileNotFoundError):
    pass


class CertificateCreationError(Exception):
    pass


class MissingKeyError(CertificateCreationError):
    pass


class MissingCertError(CertificateCreationError):
    pass


def get_cloud_settings():
    return __salt__['mc_cloud.get_cloud_settings']()


def is_wildcardable(domain):
    if domain.count('.') >= 1 and not domain.startswith('*.'):
        return True
    return False


def get_wildcard(domain):
    wdomain = None
    # try also to resolve a wildcard certificate if possible
    # and honnor that we cant wildcard TLD
    # (we should not be a subdomain of a tld domain)
    if is_wildcardable(domain):
        parts = domain.split('.')
        if len(parts) > 2:
            parts = parts[1:]
        parts.insert(0, '*')
        wdomain = '.'.join(parts)
    return wdomain


def domain_match_wildcard(domain, wildcard_or_domain):
    '''
    Test if a common name matches a wild card

        >>> from mc_states.modules.mc_ssl \\
        ...     import domain_match_wildcard as match_wildcard
        >>> match_wildcard('foo.dom.net', '*.foo.dom.net')
        True
        >>> match_wildcard('www.foo.dom.net', '*.foo.dom.net')
        True
        >>> match_wildcard('foo.dom.net', 'foo.dom.net')
        True
        >>> match_wildcard('www.foo.dom.net', 'foo.dom.net')
        True
        >>> match_wildcard('dom.net', '*.dom.net')
        True
        >>> match_wildcard('www.dom.net', '*.dom.net')
        True
        >>> match_wildcard('dom.net', 'dom.net')
        True
        >>> match_wildcard('www.dom.net', 'dom.net')
        True

    '''
    if not wildcard_or_domain.startswith('*.'):
        wildcard_or_domain = '*.' + wildcard_or_domain
    wildcard_or_domain = wildcard_or_domain.lower()
    domain = domain.lower()
    wdomain = get_wildcard(domain)
    wildcardmatch = wdomain == wildcard_or_domain
    exact_match = False
    if len(wildcard_or_domain) > 3:
        exact_match = domain == wildcard_or_domain[2:]
    return wildcardmatch or exact_match


def domain_match(domain, cert_domain, wildcard_match=False):
    '''
    Test if a domain exactly match other domain
    the other domain can be a wildcard, and
    this only match top level wildcards as per openssl spec

        >>> from mc_states.modules.mc_ssl import domain_match
        >>> domain_match('a.com', 'a.com')
        True
        >>> domain_match('a.a.com', '*.a.com')
        True
        >>> domain_match('a.a.a.com', '*.a.com')
        False
        >>> domain_match('aaa.a.com', '*.a.com')
        True
        >>> domain_match('a', '*')
        False
        >>> domain_match('a.a', '*.a')
        False
        >>> domain_match('a.com', '*.a.com')
        True
        >>> domain_match('a.com', '*.a.a.com')
        False

    '''
    ret = False
    domain = domain.lower()
    cert_domain = cert_domain.lower()
    if domain == cert_domain:
        ret = True
    if cert_domain.startswith('*.') and not ret:
        wildcard_match = True
    if wildcard_match and not ret:
        ret = domain_match_wildcard(domain, cert_domain)
    return ret


def load_key(cert_text_or_file):
    if (
        cert_text_or_file and
        ('\n' not in cert_text_or_file) and
        os.path.exists(cert_text_or_file)
    ):
        with open(cert_text_or_file) as fic:
            cert_text_or_file = fic.read()
    try:
        if 'PUBLIC' in cert_text_or_file:
            cert = load_publickey(
                OpenSSL.crypto.FILETYPE_PEM, cert_text_or_file)
        else:
            cert = OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, cert_text_or_file)
    except Exception:
        cert = None
    return cert


def load_cert(cert_text_or_file):
    if (
        cert_text_or_file and
        ('\n' not in cert_text_or_file) and
        os.path.exists(cert_text_or_file)
    ):
        with open(cert_text_or_file) as fic:
            cert_text_or_file = fic.read()
    try:
        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert_text_or_file)
    except Exception:
        cert = None
    return cert


def ssl_infos(cert_text, **kw):
    '''
    Get some infos out of a PEM certificates
    kw can contain default values

        issuer
            cert issuer
        subject
            cert subject
    '''
    data = {'cn': None,
            'altnames': [],
            'subject_r': '',
            'subject': None,
            'issuer': None,
            'issuer_r': ''}
    data.update(kw)
    cert = load_cert(cert_text)
    if cert:
        try:
            data['subject'] = cert.get_subject()
            data['subject_r'] = "{0}".format(cert.get_subject())
            data['cn'] = data['subject'].CN
        except Exception:
            pass
        try:
            dnss = get_subj_alt_name(cert)
            for i in dnss:
                data['altnames'].extend(dnss)
        except Exception:
            pass
        try:
            data['issuer'] = cert.get_issuer()
            data['issuer_r'] = "{0}".format(cert.get_issuer())
        except Exception:
            pass
        data['altnames'] = __salt__['mc_utils.uniquify'](data['altnames'])
    return data


def certificates_as_text(certificates):
    if not isinstance(certificates, list):
        certificates = [certificates]
    res2 = []
    for r in certificates:
        if len(r) > 2:
            res2.append('{0}\n{2}\n{1}'.format(*r))
        else:
            res2.append('{0}\n{1}'.format(*r))
    return res2


def certificate_as_text(certificate):
    return certificates_as_text(certificate)[0]


def ssl_keys(cert_string):
    '''
    Extract valid ssl keys from a string or a file
    '''
    if (
        cert_string and
        ('\n' not in cert_string) and
        os.path.exists(cert_string)
    ):
        with open(cert_string) as fic:
            cert_string = fic.read()
    keys = []
    if cert_string and cert_string.strip():
        (content, start_rsa, start_dsa,
         stop_pub, start_pub,
         stop_dsa, stop_rsa) = (
            '', False, False, False, False, False, False)
        for i in cert_string.splitlines():
            if '-----BEGIN PUBLIC KEY-----' in i:
                start_pub = True
            if '-----BEGIN PRIVATE KEY-----' in i:
                start_dsa = True
            if '-----BEGIN RSA PRIVATE KEY-----' in i:
                start_rsa = True
            if '-----END PUBLIC KEY-----' in i:
                stop_pub = True
            if '-----END PRIVATE KEY-----' in i:
                stop_dsa = True
            if '-----END RSA PRIVATE KEY-----' in i:
                stop_rsa = True
            if content or start_rsa or start_dsa or start_pub:
                content += i.strip()
                if not content.endswith('\n'):
                    content += '\n'
            if content and (stop_dsa or stop_rsa or stop_pub):
                ocert = load_key(content)
                if ocert is not None:
                    # valid cert
                    keys.append(content)
                (content, start_rsa, start_dsa,
                 stop_pub, start_pub,
                 stop_dsa, stop_rsa) = (
                    '', False, False, False, False, False, False)
    return keys


def ssl_key(cert_string):
    '''
    Extract valid ssl keys from a string or a file & return the first
    '''
    return ssl_keys(cert_string)[0]


def extract_certs(cert_string, common_name=None):
    if (
        cert_string and
        ('\n' not in cert_string) and
        os.path.exists(cert_string)
    ):
        with open(cert_string) as fic:
            cert_string = fic.read()
    composants, cns, full_certs = OrderedDict(), [], []
    if cert_string and cert_string.strip():
        certstring = ''
        for i in cert_string.splitlines():
            if (
                certstring or
                ('-----BEGIN CERTIFICATE-----' in i)
            ):
                certstring += i.strip()
                if not certstring.endswith('\n'):
                    certstring += '\n'
            if certstring and ('-----END CERTIFICATE-----' in i.strip()):
                ocert = load_cert(certstring)
                if ocert is not None:
                    # valid cert
                    full_certs.append(certstring)
                certstring = ''
        if full_certs:
            for ccert in full_certs:
                infos = ssl_infos(ccert)
                infos['cert'] = ccert
                try:
                    CN = infos['subject'].CN
                except Exception:
                    CN = ''
                if CN:
                    composants[CN] = infos
    # we have certificates in, and not just one
    # we can compose an ssl authentication chain
    cert_cn = None
    if composants and (len(composants) > 1):
        # filter out the domain which will not be part of the ssl chain
        for cn, data in composants.items():
            append = False
            # if we match the cert name subject, we got the cert
            # of this box
            if common_name is not None and domain_match(common_name, cn):
                cert_cn = cn
            # or we match exactly the common name
            else:
                append = True
            if append:
                cns.append(cn)
        # if we did not match the last routine,
        # assume that the real certificate is the first of the chain
        if not cns:
            for ix, cn in enumerate(composants):
                if ix == 0:
                    cert_cn = cn
                cns.append(cn)
    return full_certs, composants, cns, cert_cn


def ssl_chain(common_name, cert_string):
    '''
    Extract the cerfificate and auth chain for a certificate
    file or string containing one or multiple certificates

    Return a tuble:

        - The certificate maching the common name
          If  not found, assume the first of the given certs
        - The rest of certificates as the ssl chain authentication
    '''
    cert, chain = '', ''
    full_certs, composants, cns, cert_cn = extract_certs(
        cert_string, common_name=common_name)
    # if we have cns, we have a ssl_chain
    if cns:
        chain = ''.join([composants[cn]['cert'].strip() + '\n' for cn in cns])
        if cert_cn is None:
            cert_cn = [a for a in composants if a not in cns][0]
        if cert_cn:
            cert = composants[cert_cn]['cert']
    # else, we got a selfsigned certificate
    else:
        cert = cert_string
    return cert, chain or ''


def selfsigned_last(ctuple):
    '''
    Certificate tuple containing in first element
    the text of the PEM certificate
    '''
    data = ssl_infos(ctuple[0], subject_r='1', issuer_r='2')
    subject, issuer = data['subject_r'], data['issuer_r']
    k, v = '0', subject + ' ' + issuer
    if subject == issuer:
        k = '1'
    elif 'makina-states' in subject.lower():
        k = '1'
    elif 'makina-states' in issuer.lower():
        k = '1'
    return '{0}_{1}'.format(k, v)


def is_selfsigned(cert_string_or_path, common_name):
    selfsigned = False
    certs = extract_certs(cert_string_or_path, common_name)
    if common_name in certs[1]:
        sinfos = certs[1][common_name]
        selfsigned = sinfos['issuer_r'] == sinfos['subject_r']
    return selfsigned


def selfsigned_cert(CN,
                    bits=2048,
                    days=365,
                    C='US',
                    ST='Utah',
                    L='Salt Lake City',
                    O='SaltStack',
                    OU=None,
                    COUNTRY=None,
                    altnames=None,
                    emailAddress='xyz@pdq.net',
                    digest='sha256',
                    keytype=None):
    if COUNTRY and not C:
        C = COUNTRY
    if not altnames:
        altnames = []

    if CN.count('.') > 1:
        parts = CN.split('.')
        for alt in [
            parts[1:],
            parts
        ]:
            altn = '.'.join(alt)
            altnames.append(altn)

    alts = set()
    for i in altnames:
        if ':' not in i:
            i = 'DNS:{0}'.format(i)
        alts.add(i)

    default_keytype = 'rsa'
    if keytype is None:
        keytype = default_keytype
    cryptokeys =  {
        'rsa': (OpenSSL.crypto.TYPE_RSA, bits),
    }
    if keytype not in cryptokeys:
        keytype = default_keytype
    # create key
    key = OpenSSL.crypto.PKey()
    key.generate_key(*cryptokeys[keytype])

    # create certificate
    cert = OpenSSL.crypto.X509()
    cert.set_version(2)

    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(int(days) * 24 * 60 * 60)

    cert.get_subject().C = C
    cert.get_subject().ST = ST
    cert.get_subject().L = L
    cert.get_subject().O = O
    if OU:
        cert.get_subject().OU = OU
    cert.get_subject().CN = CN
    cert.get_subject().emailAddress = emailAddress

    if alts:
        alts = ", ".join(list(alts))
        if sys.version[0] > "2":
            cert.add_extensions([
                OpenSSL.crypto.X509Extension('subjectAltName'.encode(), False, alts.encode())])
        else:
            cert.add_extensions([
                OpenSSL.crypto.X509Extension('subjectAltName', False, alts)])

    cert.set_serial_number(1000)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, digest)
    certs = OpenSSL.crypto.dump_certificate(
        OpenSSL.crypto.FILETYPE_PEM, cert)
    keys = OpenSSL.crypto.dump_privatekey(
        OpenSSL.crypto.FILETYPE_PEM, key)
    if sys.version[0] > "2":
        certs, keys = certs.decode(), keys.decode()
    return certs, keys


def common_settings(ttl=60):
    def _do():
        _s,  _g, _o =  __salt__, __grains__, __opts__
        try:
            id_ = _s['id']
        except (TypeError, KeyError):
            id_ = _o['id']
        country = _s['grains.get']('defaultlanguage')
        if country:
            country = country[:2].upper()
        else:
            country = 'FR'
        data = _s['mc_utils.defaults'](
            PREFIX, {
                'ca': {
                    'days': 365*1000,
                    'ca_name': id_,
                    'bits': 2048,
                    'CN': _g['fqdn'],
                    'C': country,
                    'ST': 'PdL',
                    'L': 'Nantes',
                    'O': 'Makina Corpus',
                    'OU': None,
                    'emailAddress': 'contact@makina-corpus.com',
                },
                'ssl_dir': '/etc/ssl',
                'config_dir': '/etc/ssl/cloud',
                'user': 'root',
                'group': 'ssl-cert',
                'configs': {
                    '/etc/ssl/cloud/trust.sh': {
                        'target': '{config_dir}/trust.sh',
                        'mode': '750'},
                    '/etc/ssl/cloud/cleanup_certs.py': {
                        'target':
                        '{config_dir}/cleanup_certs.py',
                        'mode': '750'},
                },
                'cas': OrderedDict(),
                'email': 'root@' + _g['fqdn'],
                'domains': ["*.{0}".format(a)
                            for a in [_g['id'],
                                      _o['id'],
                                      _g['fqdn']]],
                'certificates': OrderedDict()})
        # retro compat
        data['ca']['COUNTRY'] = data['ca']['C']
        data['cert_days'] = data['ca']['days']
        data['domains'] = _s['mc_utils.uniquify'](data['domains'])
        return data
    cache_key = 'mc_ssl.common_settings'
    return deepcopy(__salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl))


def get_selfsigned_cert_for(domain,
                            gen=False,
                            keytype=None,
                            domain_csr_data=None,
                            as_text=False):
    '''
    Generate or return certificate for domain

    The certificates are stored inside a local registry
    '''
    _s = __salt__
    if keytype is None and domain.endswith('.rsa'):
        keytype = 'rsa'
    local_conf = _s['mc_macros.get_local_registry'](
        'mc_ssl_certs', registry_format='json')
    certs = local_conf.setdefault('selfsigned', {})
    if not domain.startswith('*.'):
        wdomain = get_wildcard(domain)
        if wdomain:
            try:
                return get_selfsigned_cert_for(
                    wdomain, gen=False, as_text=as_text, keytype=keytype)
            except CertificateNotFoundError:
                pass
    if domain_csr_data is None:
        domain_csr_data = {}
    csettings = common_settings()
    cert = certs.get(domain,  None)
    if cert and len(cert) < 2:
        cert = None
    if gen and not cert:
        cert = None
        domain_csr_data.setdefault('CN', domain)
        for k, val in csettings['ca'].items():
            if val and (k not in ['CN', 'days', 'ca_name']):
                domain_csr_data.setdefault(k, val)
        domain_csr_data.setdefault('days', '372000')
        domain_csr_data['keytype'] = keytype
        cert = certs[domain] = selfsigned_cert(**domain_csr_data)
        _s['mc_macros.update_local_registry'](
            'mc_ssl_certs', local_conf, registry_format='json')
    if not cert:
        raise CertificateNotFoundError(
            'Certificate not found for {0}'.format(domain))
    res = cert
    if as_text:
        res = certificate_as_text(cert)
    return res


def get_configured_cert(domain,
                        gen=False,
                        selfsigned=True,
                        ttl=60,
                        data=None,
                        as_text=False,
                        keytype=None):
    '''
    Return any configured ssl cert for domain or the wildward domain
    matching the precise domain.
    It will prefer to use any real signed certificate over a self
    signed certificate
    '''
    def _do(domain, gen, selfsigned, ttl, data):
        _s,  _g = __salt__, __grains__
        if data is None:
            data = load_extras()
        pretendants = []
        if domain == 'localhost':
            domain = _g['fqdn']
        certs = data['certificates']
        domains = [domain]
        if is_wildcardable(domain):
            wd = '*.' + '.'.join(domain.split('.')[1:])
            domains.append(wd)
        for d in domains:
            infos = certs.get(d, None)
            if not infos or len(infos) < 3:
                continue
            cert, key, chain = infos[0], infos[1], infos[2]
            if cert:
                pretendants.append((cert, key, chain))
        if not pretendants:
            if selfsigned:
                cert = get_selfsigned_cert_for(domain, gen=gen, keytype=keytype)
                pretendants.append((cert[0], cert[1], ''))
                certs[domain] = cert[0], cert[1], ''
        pretendants.sort(key=selfsigned_last)
        res = None
        if pretendants:
            res = pretendants[0]
        if res and as_text:
            res = certificate_as_text(res)
        return res
    cache_key = 'mc_ssl.get_configured_cert{0}'.format(domain)
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain, gen, selfsigned, ttl, data], {}, cache_key, ttl)


def load_extras(data=None):
    _s = __salt__
    if data is None:
        data = common_settings()
    cacerts = data.pop('cas', OrderedDict())
    dcacerts = data.setdefault('cas', OrderedDict())
    certs = data.pop('certificates', OrderedDict())
    dcerts = data.setdefault('certificates', OrderedDict())

    for cert in [a for a in cacerts]:
        cdata = cacerts[cert]
        scert, chain = cdata, ''
        if cdata[0].count('BEGIN CERTIFICATE') > 1:
            scert, chain = ssl_chain(cert, scert)
        try:
            si = ssl_infos(scert)
        except Exception:
            log.error('Error while decoding cert: {0}'.format(cert))
            continue
        dcacerts[si['cn']] = scert, chain, si

    for cert in [a for a in certs]:
        cdata = certs[cert]
        scert, chain = cdata[0], ''
        if cdata[0].count('BEGIN CERTIFICATE') > 1:
            scert, chain = ssl_chain(cert, scert)
        key = ssl_key(cdata[1])
        try:
            si = ssl_infos(scert)
        except Exception:
            log.error('Error while decoding cert: {0}'.format(cert))
            continue
        dcerts[si['cn']] = scert, key, chain, si

    is_travis = _s['mc_nodetypes.is_travis']()
    # even if we make a doublon here, it will be filtered by CN indexing
    for d in data['domains']:
        if is_travis:
            continue
        # for staging.foo.net, and we are asking
        # to generate a cert for *.staging.foo.net
        # we check that we have not already a certificate for *.foo.net
        # that would already be usable for staging.foo.net
        if d.startswith('*.'):
            uwd = d[2:]
            wduwd = get_wildcard(uwd)
            if uwd in dcerts or wduwd in dcerts:
                continue
        cert, key, chain = get_configured_cert(d, gen=True, data=data)
        try:
            si = ssl_infos(cert)
        except Exception:
            log.error('Error while decoding cert: {0}'.format(d))
            continue
        dcerts[d] = cert, key, chain, si
    # be sure to index them by the CN defined in the cert
    for cert in data['certificates']:
        cdata = data['certificates'][cert]
        try:
            cdata[2]
        except Exception:
            raise Exception('Invalid auth chain for {0}'.format(cert))
    return data


def settings():
    '''
    ssl registry

    country
        country

    st
        st

    l
        l

    o
        organization

    cn
        common name

    email
        mail

    certs
        mapping of COMMON_NAME: (cert_text, key_text, cacert_chain_txt)

            * cert_text and cacert_chain_txt contain x509 certs, concatenated
            * chain_txt is an empty string if selfsigned or not found
            * key we will validated to be a valid private key
            * all certs will be validated to be x509 certs

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = load_extras()
        return data
    return _settings()


def ssl_certs(domains, gen=False, as_text=False, keytype=None, **kw):
    '''
    Maybe Generate
    and Return SSL certificate and key paths for domain
    Certicates are generated inside pillar/cloudcontroller/<minionid>.
    this generates a signed certificate with a generated
    certificate authority with the name of the current
    minion.


    Return a xtuple (cert, key)
    Cert can contain multiple certs (full chain of certification)
    '''
    if not domains:
        raise ValueError('domains must be set')
    if isinstance(domains, six.string_types):
        domains = domains.split(',')
    ssl_certs = []
    for domain in domains:
        crt_data = get_configured_cert(domain, gen=gen, keytype=keytype, as_text=as_text)
        ssl_certs.append(crt_data)
    ssl_certs = __salt__['mc_utils.uniquify'](ssl_certs)
    return ssl_certs


def ca_ssl_certs(domains, gen=False, as_text=False, keytype=None, **kwargs):
    '''
    Wrapper to ssl_certs to also return the cacert
    information
    Return a triple (cert, key, ca)
    if ca is none: ca==''
    '''
    rdomains = []
    if isinstance(domains, six.string_types):
        domains = domains.split(',')
    for domain in domains:
        data = ssl_certs(domain, gen=gen, keytype=keytype)
        if not data:
            continue
        data = data[0]
        cert, chain = ssl_chain(domain, data[0])
        rdomains.append((cert, data[1], chain))
    if as_text:
        rdomains = certificates_as_text(rdomains)
    return rdomains


def get_cert_infos(cn_or_cert,
                   key=None,
                   sinfos=None,
                   ttl=60,
                   gen=False,
                   keytype=None,
                   trusted_certs_path=None,
                   full_certs_path=None,
                   separate_ssl_files_path=None,
                   full_basename=None,
                   auth_basename=None,
                   authr_basename=None,
                   crt_basename=None,
                   crt_full_basename=None,
                   key_basename=None,
                   bundle_basename=None,
                   only_basename=None,
                   trust_basename=None,
                   public_key_basename=None,
                   rsa_key_basename=None):
    '''
    Get infos for a certificate, either by being configured by makina-states
    or given in parameters::

        salt-call mc_ssl.get_cert_infos foo.net # configured in pillar
        salt-call -- mc_ssl.get_cert_infos \
           /tmp/devhost5-1.crt \
           key='/tmp/devhost5-1.key'
        salt-call mc_ssl.get_cert_infos -- \
            '-----BEGIN CERTIFICATE-----
            XXX
            -----END CERTIFICATE-----'\
            key='-----BEGIN PRIVATE KEY-----
            YYY
            -----END PRIVATE KEY-----'

    return a struct::

        {'cn': common name,
         'altnames': defined alt names,
         'cert_data': see bellow,
         'cert': cert + chain content,
         'crt': path where the crt should be installed,
         'trust': VALUE,
         'only': VALUE,
         'bundle': VALUE,
         'full': VALUE,
         'auth': VALUE,
         'authr': VALUE,
         'unlock_key': VALUE,
         'public_key':  public_key_or_empty_string_content,
         'rsa_key': unlocked_private_key_or_key_content,
         'key': VALUE}

    cert_data contains a 4th tuple with the certificate/key/chain contents::

        (cert,
         key,
         chain_or_empty_string)

    '''
    _s = __salt__
    def _do(cn_or_cert,
            key,
            sinfos,
            gen,
            keytype,
            trusted_certs_path,
            full_certs_path,
            separate_ssl_files_path,
            full_basename,
            auth_basename,
            authr_basename,
            crt_basename,
            crt_full_basename,
            key_basename,
            bundle_basename,
            only_basename,
            trust_basename,
            public_key_basename,
            rsa_key_basename):
        settings = common_settings()
        keyc = key
        cn_or_certc = None
        if key:
            if '\n' in key:
                keyc = key.replace(' ', '\n')
                keyc = key.replace(
                    'BEGIN\nPRIVATE', 'BEGIN PRIVATE')
                keyc = key.replace(
                    'END\nPRIVATE', 'END PRIVATE')
                keyc = key.replace(
                    '\nKEY', ' KEY')
            elif os.path.exists(key):
                with open(key) as f:
                    keyc = f.read()
            else:
                raise CertificateFileNotFoundError(
                    'invalid key {0}'.format(key))
        if 'BEGIN' in cn_or_cert:
            cn_or_certc = cn_or_cert.replace(' ', '\n')
            cn_or_certc = cn_or_cert.replace(
                'BEGIN\nCERT', 'BEGIN CERT')
            cn_or_certc = cn_or_cert.replace(
                'END\nCERT', 'END CERT')
        elif (
            os.path.exists(cn_or_cert) and '\n' not in cn_or_cert
        ):
            with open(cn_or_cert) as f:
                cn_or_certc = f.read()
        if cn_or_certc:
            if sinfos is None:
                sinfos = ssl_infos(cn_or_certc)
            cert, chain = ssl_chain(sinfos['cn'], cn_or_certc)
            cdata = (cert, keyc, chain)
        else:
            cdata = get_configured_cert(cn_or_cert, gen=gen, keytype=keytype)
            if sinfos is None:
                sinfos = ssl_infos(cdata[0])
        cn = sinfos['cn']
        altnames = sinfos.get('altnames', [])
        if not cn:
            raise CertificateNotFoundError(
                '{0} is not valid'.format(cn_or_cert))
        if not separate_ssl_files_path:
            separate_ssl_files_path = os.path.join(settings['config_dir'],
                                                   'separate')
        if not full_certs_path:
            full_certs_path = os.path.join(settings['config_dir'], 'certs')
        if not trusted_certs_path:
            trusted_certs_path = os.path.join(settings['config_dir'], 'trust')
        cdata = [a for a in cdata]
        # try to get the unlocked version of the private key
        pkey = None
        public_key = ''
        private_key = ''
        if cdata[1]:
            pkey = load_key(cdata[1])
        if pkey:
            try:
                ossl = subprocess.Popen(['openssl', 'rsa', '-pubout'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        stdin=subprocess.PIPE)
                (stdout, stderr) = ossl.communicate(cdata[1])
                ossl.wait()
                if ossl.returncode == 0 and ('BEGIN PUBLIC KEY' in stdout):
                    keys = ssl_keys(stdout)
                    if keys:
                        public_key = keys[0]
            except Exception:
                trace = traceback.format_exc()
                log.error('INFOS public private key for {0}'.format(cn))
                log.error(trace)
            try:
                ossl = subprocess.Popen(['openssl', 'rsa'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        stdin=subprocess.PIPE)
                (stdout, stderr) = ossl.communicate(cdata[1])
                ossl.wait()
                if (
                    ossl.returncode == 0 and
                    ('BEGIN RSA PRIVATE KEY' in stdout)
                ):
                    keys = ssl_keys(stdout)
                    if keys:
                        private_key = keys[0]
            except Exception:
                trace = traceback.format_exc()
                log.error('INFOS rsa private key for {0}'.format(cn))
                log.error(trace)
        ret = {'cn': cn,
                'altnames': altnames,
                'cert_data': cdata,
                'rsa_key': private_key,
                'public_key': public_key,
                'cert': '\n'.join([cdata[0], cdata[2] or '']),
                'crt': '{0}/{1}'.format(
                    full_certs_path,
                    full_basename or '{0}.crt'.format(cn)),
                'trust': '{0}/{1}'.format(
                    trusted_certs_path,
                    '{0}.crt'.format(cn)),
                'only': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    only_basename or '{0}.crt'.format(cn)),
                'bundle': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    bundle_basename or '{0}-bundle.crt'.format(cn)),
                'full': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    crt_full_basename or '{0}-full.crt'.format(cn)),
                'auth': '{0}/{1}'.format(
                     separate_ssl_files_path,
                    auth_basename or '{0}-auth.crt'.format(cn)),
                'authr': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    authr_basename or '{0}-authr.crt'.format(cn)),
                'rsa_keyp': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    rsa_key_basename or '{0}.rsa-key'.format(cn)),
                'public_keyp': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    public_key_basename or '{0}.public-key'.format(cn)),
                'key': '{0}/{1}'.format(
                    separate_ssl_files_path,
                    key_basename or '{0}.key'.format(cn)),
                'has_chain': bool((cdata[2] or '').strip())}
        return ret
    cache_key = 'mc_ssl.get_cert_infos{0}{1}'.format(
        cn_or_cert.replace('\n', ''),
        (key or '').replace('\n', ''),
    )
    return _s['mc_utils.memoize_cache'](
        _do, [
            cn_or_cert,
            key,
            sinfos,
            gen,
            keytype,
            trusted_certs_path,
            full_certs_path,
            separate_ssl_files_path,
            full_basename,
            auth_basename,
            authr_basename,
            crt_basename,
            crt_full_basename,
            key_basename,
            bundle_basename,
            only_basename,
            trust_basename,
            public_key_basename,
            rsa_key_basename],
        {}, cache_key, ttl)
# vim:set et sts=4 ts=4 tw=80:
