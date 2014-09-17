#!/usr/bin/env python
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
from copy import deepcopy
import os
from salt.utils.odict import OrderedDict
import mc_states.utils
import M2Crypto
try:
    import OpenSSL
    HAS_SSL = True
except:
    HAS_SSL = False


__name = 'ssl'
log = logging.getLogger(__name__)


class CertificateNotFoundError(Exception):
    pass


class CertificateCreationError(Exception):
    pass


class MissingKeyError(CertificateCreationError):
    pass


class MissingCertError(CertificateCreationError):
    pass


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
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        # users data
        # SSL settings for reuse in states
        country = saltmods['grains.get']('defaultlanguage')
        if country:
            country = country[:2].upper()
        else:
            country = 'fr'
        data = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.ssl', {
                'country': country,
                'st': 'Pays de Loire',
                'l': 'NANTES',
                'o': 'NANTES',
                'cn': grains['fqdn'],
                'email': grains['fqdn'],
            })
        return data
    return _settings()


def ensure_ca_present():
    cloudSettings = __salt__['mc_cloud.settings']()
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    old_d = __opts__.get('ca.cert_base_path', '')
    try:
        __salt__['tls.set_ca_path'](ssl_gen_d)
        if not __salt__['tls.ca_exists'](cloudSettings['ssl']['ca']['ca_name']):
            ret = __salt__['tls.create_ca'](**cloudSettings['ssl']['ca'])
            lret = ret.lower()
            if not (('already' in lret) or ('created' in lret)):
                raise CertificateCreationError(
                    'Failed to create ca cert for cloud controller')
    finally:
        __salt__['tls.set_ca_path'](old_d)


def get_cacert(as_text=False):
    cloudSettings = __salt__['mc_cloud.settings']()
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    old_d = __opts__.get('ca.cert_base_path', '')
    path = None
    try:
        __salt__['tls.set_ca_path'](ssl_gen_d)
        ensure_ca_present()
        path = __salt__['tls.get_ca'](
            cloudSettings['ssl']['ca']['ca_name'],
            as_text=as_text)
    finally:
        __salt__['tls.set_ca_path'](old_d)
    return path


def get_cert_for(domain, gen=False, domain_csr_data=None):
    '''Generate or return certificate for domain'''
    ensure_ca_present()
    if domain_csr_data is None:
        domain_csr_data = {}
    cloudSettings = __salt__['mc_cloud.settings']()
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    ca = cloudSettings['ssl']['ca']['ca_name']
    certp = os.path.join(ssl_gen_d, ca, 'certs', '{0}.crt'.format(domain))
    bcertp = os.path.join(ssl_gen_d, ca, 'certs', '{0}.bundle.crt'.format(domain))
    certk = os.path.join(ssl_gen_d, ca, 'certs', '{0}.key'.format(domain))
    cacertp = os.path.join(ssl_gen_d, ca, '{0}_ca_cert.crt'.format(ca))
    selfsigned = False
    if gen and not os.path.exists(certp):
        selfsigned = True
        old_d = __opts__.get('ca.cert_base_path', '')
        try:
            __salt__['tls.set_ca_path'](ssl_gen_d)
            if not __salt__['tls.ca_exists'](cloudSettings['ssl']['ca']['ca_name']):
                ret = __salt__['tls.create_ca'](**cloudSettings['ssl']['ca'])
                lret = ret.lower()
                if not (('already' in lret) or ('created' in lret)):
                    raise CertificateCreationError(
                        'Failed to create ca cert for cloud controller')
            domain_csr_data.setdefault('CN', domain)
            for k, val in cloudSettings['ssl']['ca'].items():
                if val and (k not in ['CN', 'days', 'ca_name']):
                    domain_csr_data.setdefault(k, val)
            csr = __salt__['tls.create_csr'](ca, **domain_csr_data)
            lcsr = csr.lower()
            if not (('already' in lcsr) or ('created' in lcsr)):
                raise CertificateCreationError(
                    'Failed to create ca cert for cloud controller')
            __salt__['tls.create_ca_signed_cert'](
                ca, domain, cloudSettings['ssl']['cert_days'])
        finally:
            __salt__['tls.set_ca_path'](old_d)
    if not os.path.exists(certp):
        raise CertificateNotFoundError(
            'Certificate not found for {0}'.format(domain))
    if selfsigned and not os.path.exists(bcertp) and os.path.exists(cacertp):
        data = ''
        for f in [cacertp, certp]:
            with open(f) as fic:
                data += fic.read()
            with open(bcertp, 'w') as fic:
                fic.write(data)
    #if os.path.exists(bcertp):
    #    certp = bcertp
    return certp, certk


def get_selfsigned_cert_for(domain, gen=False, domain_csr_data=None):
    '''Generate or return certificate for domain'''
    ensure_ca_present()
    if domain_csr_data is None:
        domain_csr_data = {}
    cloudSettings = __salt__['mc_cloud.settings']()
    ssl_gen_d = get_selfsigned_certs_dir()
    certp = os.path.join(ssl_gen_d, 'certs', '{0}.crt'.format(domain))
    certk = os.path.join(ssl_gen_d, 'certs', '{0}.key'.format(domain))
    if gen and not os.path.exists(certp):
        old_d = __opts__.get('ca.cert_base_path', '')
        try:
            __salt__['tls.set_ca_path'](ssl_gen_d)
            domain_csr_data.setdefault('CN', domain)
            for k, val in cloudSettings['ssl']['ca'].items():
                if val and (k not in ['CN', 'days', 'ca_name']):
                    domain_csr_data.setdefault(k, val)
            ret = __salt__['tls.create_self_signed_cert'](tls_dir='', **domain_csr_data)
        finally:
            __salt__['tls.set_ca_path'](old_d)
    if not os.path.exists(certp):
        raise CertificateNotFoundError(
            'Certificate not found for {0}'.format(domain))
    return certp, certk


def is_certificate_matching_domain(cert_path, domain):
    ret = False
    return ret


def domain_match(domain, cert_domain):
    '''Test if a domain exactly match other domain
    the other domain can be a wildcard, and
    this only match top level wildcards as per openssl spec::

        >>> domain_match('a.com', 'a.com')
        True
        >>> domain_match('a.com', '*.a.com')
        False
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
    '''
    ret = False
    if domain.lower() == cert_domain.lower():
        ret = True
    if cert_domain.startswith('*.'):
        parts = cert_domain.split('.')
        dparts = domain.split('.')
        if (
            (len(parts) == len(dparts))
            and (len(parts) > 2)
            and dparts[1:] == parts[1:]
        ):
            ret = True
    return ret


def load_certs(path):
    '''
    Load certificates from a directory (certs must be suffixed with .crt)
    return 2 dictionnary:

            - one contains certs with common name as indexes
            - one contains certs with subjectaltnames as indexes
    '''
    exacts = {}
    alts = {}
    certs_dir = get_certs_dir()
    if certs_dir and not os.path.exists(certs_dir):
        os.makedirs(certs_dir)
    for cert in os.listdir(path):
        if not cert.endswith('.crt'):
            continue
        certp = os.path.join(certs_dir, cert)
        certk = os.path.join(certs_dir, "{0}.key".format(cert[:-4]))
        certo = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, open(certp).read())
        for i in ("{0}".format(certo.get_subject())).split('/'):
            data = {'key': certk, 'cert': certp}
            certo = M2Crypto.X509.load_cert(certp)
            if i.startswith('CN='):
                cn = i.split('CN=')[1]
                if cn not in exacts:
                    exacts[cn] = data
        try:
            ext = certo.get_ext('subjectAltName')
            for ev in ext.get_value().split(','):
                if ev.startswith('DNS:'):
                    cn = ''.join(ev.split('DNS:')[1:])
                    if cn not in alts:
                        alts[cn] = data
        except LookupError:
            pass
    return exacts, alts


def load_selfsigned_certs(path):
    '''
    Load certificates from a directory (certs must be suffixed with .crt)
    return 2 dictionnary:

            - one contains certs with common name as indexes
            - one contains certs with subjectaltnames as indexes
    '''
    exacts = {}
    alts = {}
    certs_dir = get_selfsigned_certs_dir()
    if certs_dir and not os.path.exists(certs_dir):
        os.makedirs(certs_dir)
    for cert in os.listdir(path):
        if not cert.endswith('.crt'):
            continue
        certp = os.path.join(certs_dir, cert)
        certk = os.path.join(certs_dir, "{0}.key".format(cert[:-4]))
        certo = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, open(certp).read())
        for i in ("{0}".format(certo.get_subject())).split('/'):
            data = {'key': certk, 'cert': certp}
            certo = M2Crypto.X509.load_cert(certp)
            if i.startswith('CN='):
                cn = i.split('CN=')[1]
                if cn not in exacts:
                    exacts[cn] = data
        try:
            ext = certo.get_ext('subjectAltName')
            for ev in ext.get_value().split(','):
                if ev.startswith('DNS:'):
                    cn = ''.join(ev.split('DNS:')[1:])
                    if cn not in alts:
                        alts[cn] = data
        except LookupError:
            pass
    return exacts, alts


def get_selfsigned_certs_dir():
    cloudSettings = __salt__['mc_cloud.settings']()
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    certs_dir = os.path.join(ssl_gen_d, 'selfsigned')
    return certs_dir


def get_certs_dir():
    cloudSettings = __salt__['mc_cloud.settings']()
    ca = cloudSettings['ssl']['ca']['ca_name']
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    certs_dir = os.path.join(ssl_gen_d, ca, 'certs')
    return certs_dir


def search_matching_certificate(domain, as_text=False):
    '''Search in the pillar certificate directory the
    certificate belonging to a particular domain'''
    if not HAS_SSL:
        raise Exception('Missing pyopenssl')
    certs_dir = get_certs_dir()
    certp, certk = None, None
    # try to get a exact-matchinf filename<->domain
    try:
        certp, certk = get_cert_for(domain)
    except CertificateNotFoundError:
        pass
    # parse certificates to see if we can find an exactly but misnamed cert
    if not certp:
        exacts, alts = load_certs(certs_dir)
        for cert_domain in exacts:
            if domain_match(domain, cert_domain):
                data = exacts[cert_domain]
                certp, certk = data['cert'], data['key']
                break
    # parse certificates to see if we can find a certificate
    # with a subjectAltName extension matching our domain
    if not certp:
        for cert_domain in alts:
            if domain_match(domain, cert_domain):
                data = alts[cert_domain]
                certp, certk = data['cert'], data['key']
                break
    # last resort, try to generate a certificate throught our CA
    if not certp:
        certp, certk = get_cert_for(domain, gen=True)
    if (not certp) or (certp and not os.path.exists(certp)):
        raise MissingCertError(
            '{1}: Missing cert: {0}'.format(certp, domain))
    if (not certk) or (certk and not os.path.exists(certk)):
        raise MissingKeyError(
            '{1}: Missing private key for cert: {0}'.format(certp, domain))
    if as_text:
        with open(certp) as fic:
            certp = fic.read()
        with open(certk) as fic:
            certk = fic.read()
    return certp, certk


def search_matching_selfsigned_certificate(domain, as_text=False):
    '''Search in the pillar certificate directory the
    certificate belonging to a particular domain'''
    if not HAS_SSL:
        raise Exception('Missing pyopenssl')
    certs_dir = get_selfsigned_certs_dir()
    certp, certk = None, None
    # try to get a exact-matchinf filename<->domain
    try:
        certp, certk = get_selfsigned_cert_for(domain)
    except CertificateNotFoundError:
        pass
    # parse certificates to see if we can find an exactly but misnamed cert
    if not certp:
        exacts, alts = load_selfsigned_certs(certs_dir)
        for cert_domain in exacts:
            if domain_match(domain, cert_domain):
                data = exacts[cert_domain]
                certp, certk = data['cert'], data['key']
                break
    # parse certificates to see if we can find a certificate
    # with a subjectAltName extension matching our domain
    if not certp:
        for cert_domain in alts:
            if domain_match(domain, cert_domain):
                data = alts[cert_domain]
                certp, certk = data['cert'], data['key']
                break
    # last resort, try to generate a certificate throught our CA
    if not certp:
        certp, certk = get_selfsigned_cert_for(domain, gen=True)
    if (not certp) or (certp and not os.path.exists(certp)):
        raise MissingCertError(
            '{1}: Missing cert: {0}'.format(certp, domain))
    if (not certk) or (certk and not os.path.exists(certk)):
        raise MissingKeyError(
            '{1}: Missing private key for cert: {0}'.format(certp, domain))
    if as_text:
        with open(certp) as fic:
            certp = fic.read()
        with open(certk) as fic:
            certk = fic.read()
    return certp, certk


def selfsigned_ssl_certs(domains, as_text=False):
    '''
    Maybe Generate
    and Return SSL certificate and key paths for domain
    Certicates are generated inside pillar/cloudcontroller/<minionid>.
    this generates a signed certificate with a generated
    certificate authority with the name of the current
    minion.
    '''
    if not domains:
        raise ValueError('domains must be set')
    if isinstance(domains, basestring):
        domains = domains.split(',')
    ssl_certs = []
    for domain in domains:
        crt_data = search_matching_selfsigned_certificate(
            domain, as_text=as_text)
        if crt_data not in ssl_certs:
            ssl_certs.append(crt_data)
    return ssl_certs



def ssl_certs(domains, as_text=False):
    '''
    Maybe Generate
    and Return SSL certificate and key paths for domain
    Certicates are generated inside pillar/cloudcontroller/<minionid>.
    this generates a signed certificate with a generated
    certificate authority with the name of the current
    minion.
    '''
    if not domains:
        raise ValueError('domains must be set')
    if isinstance(domains, basestring):
        domains = domains.split(',')
    ssl_certs = []
    for domain in domains:
        crt_data = search_matching_certificate(
            domain, as_text=as_text)
        if crt_data not in ssl_certs:
            ssl_certs.append(crt_data)
    return ssl_certs


def ca_ssl_certs(domains, as_text=False):
    '''
    Wrapper to ssl_certs to also return the cacert
    information
    '''

    cacert = get_cacert(as_text=as_text)
    rdomains = []
    for domain in ssl_certs(domains, as_text=as_text):
        rdomains.append((cacert,) + domain)
    return rdomains


def dump():
    return mc_states.utils.dump(__salt__,__name)

# vim:set et sts=4 ts=4 tw=80:
