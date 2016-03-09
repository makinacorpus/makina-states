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
import mc_states.api
try:
    import OpenSSL
    HAS_SSL = True
except:
    HAS_SSL = False


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
    if domain.count('.') >= 2 and not domain.startswith('*.'):
        return True
    return False


def get_wildcard(domain):
    wdomain = None
    # try also to resolve a wildcard certificate if possible
    # and honnor that we cant wildcard TLD (we should not be a subdomain of a tld domain)
    if is_wildcardable(domain):
        wdomain = '*.' + '.'.join(domain.split('.')[1:])
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
        cert_text_or_file
        and ('\n' not in cert_text_or_file)
        and os.path.exists(cert_text_or_file)
    ):
        with open(cert_text_or_file) as fic:
            cert_text_or_file = fic.read()
    try:
        cert = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, cert_text_or_file)
    except Exception:
        cert = None
    return cert


def load_cert(cert_text_or_file):
    if (
        cert_text_or_file
        and ('\n' not in cert_text_or_file)
        and os.path.exists(cert_text_or_file)
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
    data = {'subject_r': '',
            'subject': None,
            'issuer': None,
            'issuer_r': ''}
    data.update(kw)
    cert = load_cert(cert_text)
    if cert:
        try:
            data['subject'] = cert.get_subject()
            data['subject_r'] = "{0}".format(cert.get_subject())
        except Exception:
            pass
        try:
            data['issuer'] = cert.get_issuer()
            data['issuer_r'] = "{0}".format(cert.get_issuer())
        except Exception:
            pass
    return data


def ssl_keys(cert_string):
    '''
    Extract valid ssl keys from a string or a file
    '''
    if (
        cert_string
        and ('\n' not in cert_string)
        and os.path.exists(cert_string)
    ):
        with open(cert_string) as fic:
            cert_string = fic.read()
    keys = []
    if cert_string and cert_string.strip():
        content, start_rsa, start_dsa, stop_dsa, stop_rsa = (
            '', False, False, False, False)
        for i in cert_string.splitlines():
            if '-----BEGIN PRIVATE KEY-----' in i:
                start_dsa = True
            if '-----BEGIN RSA PRIVATE KEY-----' in i:
                start_rsa = True
            if '-----END PRIVATE KEY-----' in i:
                stop_dsa = True
            if '-----END RSA PRIVATE KEY-----' in i:
                stop_rsa = True
            if content or start_rsa or start_dsa:
                content += i.strip()
                if not content.endswith('\n'):
                    content += '\n'
            if content and (stop_dsa or stop_rsa):
                ocert = load_key(content)
                if ocert is not None:
                    # valid cert
                    keys.append(content)
                content, start_rsa, start_dsa, stop_dsa, stop_rsa = (
                    '', False, False, False, False)
    return keys


def ssl_key(cert_string):
    '''
    Extract valid ssl keys from a string or a file & return the first
    '''
    return ssl_keys(cert_string)[0]


def extract_certs(cert_string, common_name=None):
    if (
        cert_string
        and ('\n' not in cert_string)
        and os.path.exists(cert_string)
    ):
        with open(cert_string) as fic:
            cert_string = fic.read()
    composants, cns, full_certs = OrderedDict(), [], []
    if cert_string and cert_string.strip():
        certstring = ''
        for i in cert_string.splitlines():
            if (
                certstring
                or ('-----BEGIN CERTIFICATE-----' in i)
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
    return cert, chain


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


def ensure_ca_present():
    cloudSettings = get_cloud_settings()
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
    cloudSettings = get_cloud_settings()
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


def is_selfsigned(ssl_gen_d, domain):
    selfsigned = False
    for cert in [
        os.path.join(
            ssl_gen_d, '{0}.crt'.format(domain)),
        os.path.join(
            ssl_gen_d, '{0}.full.crt'.format(domain)),
        os.path.join(
            ssl_gen_d, '{0}.auth.crt'.format(domain)),
        os.path.join(
            ssl_gen_d, '{0}.bundle.crt'.format(domain)),
        os.path.join(
            ssl_gen_d, '{0}-full.crt'.format(domain)),
        os.path.join(
            ssl_gen_d, '{0}-auth.crt'.format(domain)),
        os.path.join(
            ssl_gen_d, '{0}-bundle.crt'.format(domain))
    ]:
        if os.path.exists(cert):
            certs = extract_certs(cert, domain)
            if domain in certs[1]:
                sinfos = certs[1][domain]
                selfsigned = sinfos['issuer_r'] == sinfos['subject_r']
                break
    return selfsigned


def get_installed_cert_for(domain):
    '''
    Seach for certificate and key file inside pillar folder

    pillarroot/cloud-controller/ssl/custom:

        <domain>.key
            contain private ,key
        <domain>.crt
            contain cert
        <domain>.auth.crt
            contain auth chain
        <domain>.bundle.crt
            <generated if not present>
            contain cert + auth chain
        <domain>.full.crt
            <generated if not present>
            contain cert + auth chain + key
    '''
    ssl_gen_d = "/etc/ssl/cloud/separate"
    fcertp = os.path.join(
        ssl_gen_d, '{0}-full.crt'.format(domain))
    acertp = os.path.join(
        ssl_gen_d, '{0}-auth.crt'.format(domain))
    certp = os.path.join(
        ssl_gen_d, '{0}.crt'.format(domain))
    bcertp = os.path.join(
        ssl_gen_d, '{0}-bundle.crt'.format(domain))
    certk = os.path.join(
        ssl_gen_d, '{0}.key'.format(domain))
    wdomain = get_wildcard(domain)
    if wdomain:
        wfcertp = os.path.join(
            ssl_gen_d, '{0}-full.crt'.format(wdomain))
        wacertp = os.path.join(
            ssl_gen_d, '{0}-auth.crt'.format(wdomain))
        wcertp = os.path.join(
            ssl_gen_d, '{0}.crt'.format(wdomain))
        wbcertp = os.path.join(
            ssl_gen_d, '{0}-bundle.crt'.format(wdomain))
        wcertk = os.path.join(
            ssl_gen_d, '{0}.key'.format(wdomain))
        if os.path.exists(wbcertp):
            wcertp = wbcertp
        # only use wild card
        # - if the more precise cert is selfsigned
        #   but the wildcarded one is signed
        # - if we have not a more precise certificate
        if os.path.exists(wcertp):
            if not os.path.exists(certp) and not os.path.exists(bcertp):
                use_wildcard = True
            else:
                if (
                    is_selfsigned(ssl_gen_d, domain)
                    and not is_selfsigned(ssl_gen_d, wdomain)
                ):
                    use_wildcard = True
            if use_wildcard:
                fcertp = wfcertp
                acertp = wacertp
                bcertp = wbcertp
                certp = wcertp
                certk = wcertk
    if not os.path.exists(bcertp):
        content = ''
        for fil in [certp, acertp]:
            if not os.path.exists(fil):
                raise CertificateFileNotFoundError(
                    'Cert info is not valid for {0} ({1})'.format(domain, fil))
            with open(fil) as fic:
                content += fic.read()
            if not content.endswith('\n'):
                content += '\n'
        if content.strip():
            with open(bcertp, 'w') as fic:
                fic.write(content)
        else:
            raise CertificateFileNotFoundError(
                'Cert info is not valid for {0}'.format(domain))
    if not os.path.exists(fcertp):
        content = ''
        for fil in [bcertp, certk]:
            if not os.path.exists(fil):
                raise CertificateKeyFileNotFoundError(
                    'Cert info is not valid for {0} ({1})'.format(domain, fil))
            with open(fil) as fic:
                content += fic.read()
            if not content.endswith('\n'):
                content += '\n'
        if content.strip():
            with open(fcertp, 'w') as wfic:
                wfic.write(content)
        else:
            raise CertificateKeyFileNotFoundError(
                'Cert info is not valid for {0}'.format(domain))
    if os.path.exists(bcertp):
        certp = bcertp
    for item in [certk, fcertp]:
        if os.path.exists(item):
            os.chmod(item, 0770)
    for i in [certp, certk]:
        if not os.path.exists(i):
            raise CertificateNotFoundError(
                "No such custom cert for '{0}'".format(domain))
    return certp, certk


def get_custom_cert_for(domain):
    '''
    Seach for certificate and key file inside pillar folder

    pillarroot/cloud-controller/ssl/custom:

        <domain>.key
            contain private ,key
        <domain>.crt
            contain cert
        <domain>.auth.crt
            contain auth chain
        <domain>.bundle.crt
            <generated if not present>
            contain cert + auth chain
        <domain>.full.crt
            <generated if not present>
            contain cert + auth chain + key
    '''

    cloudSettings = get_cloud_settings()
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    fcertp = os.path.join(
        ssl_gen_d, 'custom', '{0}.full.crt'.format(domain))
    acertp = os.path.join(
        ssl_gen_d, 'custom', '{0}.auth.crt'.format(domain))
    certp = os.path.join(
        ssl_gen_d, 'custom', '{0}.crt'.format(domain))
    bcertp = os.path.join(
        ssl_gen_d, 'custom', '{0}.bundle.crt'.format(domain))
    certk = os.path.join(
        ssl_gen_d, 'custom', '{0}.key'.format(domain))
    wdomain = get_wildcard(domain)
    if wdomain:
        wfcertp = os.path.join(
            ssl_gen_d, 'custom', '{0}.full.crt'.format(wdomain))
        wacertp = os.path.join(
            ssl_gen_d, 'custom', '{0}.auth.crt'.format(wdomain))
        wcertp = os.path.join(
            ssl_gen_d, 'custom', '{0}.crt'.format(wdomain))
        wbcertp = os.path.join(
            ssl_gen_d, 'custom', '{0}.bundle.crt'.format(wdomain))
        wcertk = os.path.join(
            ssl_gen_d, 'custom', '{0}.key'.format(wdomain))
        if os.path.exists(wbcertp):
            wcertp = wbcertp
        # only use wild card if we have not a more precise certificate
        if not os.path.exists(certp) and not os.path.exists(bcertp):
            fcertp = wfcertp
            acertp = wacertp
            bcertp = wbcertp
            certp = wcertp
            certk = wcertk
    if not os.path.exists(bcertp):
        content = ''
        for fil in [certp, acertp]:
            if not os.path.exists(fil):
                raise CertificateFileNotFoundError(
                    'Cert info is not valid for {0} ({1})'.format(domain, fil))
            with open(fil) as fic:
                content += fic.read()
            if not content.endswith('\n'):
                content += '\n'
        if content.strip():
            with open(bcertp, 'w') as fic:
                fic.write(content)
        else:
            raise CertificateFileNotFoundError(
                'Cert info is not valid for {0}'.format(domain))
    if not os.path.exists(fcertp):
        content = ''
        for fil in [bcertp, certk]:
            if not os.path.exists(fil):
                raise CertificateKeyFileNotFoundError(
                    'Cert info is not valid for {0} ({1})'.format(domain, fil))
            with open(fil) as fic:
                content += fic.read()
            if not content.endswith('\n'):
                content += '\n'
        if content.strip():
            with open(fcertp, 'w') as wfic:
                wfic.write(content)
        else:
            raise CertificateKeyFileNotFoundError(
                'Cert info is not valid for {0}'.format(domain))
    if os.path.exists(bcertp):
        certp = bcertp
    for item in [certk, fcertp]:
        if os.path.exists(item):
            os.chmod(item, 0770)
    for i in [certp, certk]:
        if not os.path.exists(i):
            raise CertificateNotFoundError(
                "No such custom cert for '{0}'".format(domain))
    return certp, certk


def get_cert_for(domain, gen=False, domain_csr_data=None):
    '''
    Generate or return certificate for domain

    The certificates are stored inside <pillar_root>/cloud-controller/ssl

    Search order precedence:

      - ./custom/<subdomain>.<domain>.<tld>
      - wildcard certificate: ./custom/\*.<domain>.<tld>
      - signed by the controller: ./<cloudctlr>/certs/\*.<domain>.<tld>
      - signed by the controller: ./<cloudctlr>/certs/<sub>.<domain>.<tld>

    '''
    try:
        return get_custom_cert_for(domain)
    except CertificateNotFoundError:
        pass
    if not domain.startswith('*.'):
        wdomain = get_wildcard(domain)
        if wdomain:
            try:
                return get_cert_for(wdomain)
            except CertificateNotFoundError:
                pass
    ensure_ca_present()
    if domain_csr_data is None:
        domain_csr_data = {}
    cloudSettings = get_cloud_settings()
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    ca = cloudSettings['ssl']['ca']['ca_name']
    certp = os.path.join(ssl_gen_d, ca, 'certs', '{0}.crt'.format(domain))
    bcertp = os.path.join(ssl_gen_d, ca, 'certs', '{0}.bundle.crt'.format(domain))
    certk = os.path.join(ssl_gen_d, ca, 'certs', '{0}.key'.format(domain))
    cacertp = os.path.join(ssl_gen_d, ca, '{0}_ca_cert.crt'.format(ca))
    generated = False
    if gen and not os.path.exists(certp):
        generated = True
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
    # generate bundle
    if (
        generated
        and os.path.exists(cacertp)
        and os.path.exists(certp)
        and not os.path.exists(bcertp)
    ):
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
    '''
    Generate or return certificate for domain

    The certificates are stored inside <pillar_root>/cloud-controller/ssl

    Search precedence:

      - ./custom/<subdomain>.<domain>.<tld>
      - wildcard certificate: ./custom/\*.<domain>.<tld>
      - selfsigned: ./selfsigned/certs/\*.<domain>.<tld>
      - selfsigned: ./selfsigned/certs/<subdomain>.<domain>.<tld>

    '''
    try:
        return get_custom_cert_for(domain)
    except CertificateNotFoundError:
        pass
    if not domain.startswith('*.'):
        wdomain = get_wildcard(domain)
        if wdomain:
            try:
                return get_selfsigned_cert_for(wdomain, gen=False)
            except CertificateNotFoundError:
                pass
    #ensure_ca_present()
    if domain_csr_data is None:
        domain_csr_data = {}
    cloudSettings = get_cloud_settings()
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
            domain_csr_data.setdefault('days', '372000')
            ret = __salt__['tls.create_self_signed_cert'](tls_dir='', **domain_csr_data)
        finally:
            __salt__['tls.set_ca_path'](old_d)
    if not os.path.exists(certp):
        raise CertificateNotFoundError(
            'Certificate not found for {0}'.format(domain))
    return certp, certk


def load_certs(path):
    '''
    Load certificates from a directory (certs must be suffixed with .crt)
    return 2 dictionnary:

            - one contains certs with common name as indexes
            - one contains certs with subjectaltnames as indexes
    '''
    exacts = {}
    alts = {}
    if path and not os.path.exists(path):
        os.makedirs(path)
    for cert in os.listdir(path):
        if not cert.endswith('.crt'):
            continue
        certp = os.path.join(path, cert)
        certk = os.path.join(path, "{0}.key".format(cert[:-4]))
        try:
            certo = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, open(certp).read())
        except:
            log.error('problem with {0}'.format(certp))
            continue
        for i in ("{0}".format(certo.get_subject())).split('/'):
            data = {'key': certk, 'cert': certp}
            try:
                certo = OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_PEM, open(certp).read())
            except:
                log.error('problem with {0}'.format(certp))
                continue
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
            certo = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, open(certp).read()) 
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
    return os.path.join(get_cloud_settings()['ssl_pillar_dir'], 'selfsigned')


def get_certs_dir():
    cloudSettings = get_cloud_settings()
    ca = cloudSettings['ssl']['ca']['ca_name']
    ssl_gen_d = cloudSettings['ssl_pillar_dir']
    certs_dir = os.path.join(ssl_gen_d, ca, 'certs')
    return certs_dir


def get_custom_certs_dir():
    return os.path.join(get_cloud_settings()['ssl_pillar_dir'], 'custom')


def search_matching_certificate(domain, as_text=False, selfsigned=True):
    '''
    Search in the pillar certificate directory the
    certificate belonging to a particular domain
    '''
    if not HAS_SSL:
        raise Exception('Missing pyopenssl')
    certp, certk = None, None
    # try to get a exact-matching filename<->domain
    if not certp:
        try:
            certp, certk = get_custom_cert_for(domain)
        except CertificateNotFoundError:
            pass
    # try to get a selfsigned cert
    if not certp:
        try:
            certp, certk = get_selfsigned_cert_for(domain)
        except CertificateNotFoundError:
            pass
    # try to get a exact-matching filename<->domain
    # signed by the local CA
    if not certp:
        try:
            certp, certk = get_cert_for(domain)
        except CertificateNotFoundError:
            pass
    # try to see if someone has installed a full certificate containing
    # at least the cert and key but also the auth chain in
    # the well known install dir
        try:
            certp, certk = get_installed_cert_for(domain)
        except CertificateNotFoundError:
            pass
    # parse certificates to see if we can find an exactly but misnamed cert
    exacts, alts = [], []
    if not certp:
        for certs_dir in [
            get_custom_certs_dir(),
            get_selfsigned_certs_dir(),
            get_certs_dir(),
        ]:
            _exacts, _alts = load_certs(certs_dir)
            exacts.extend(_exacts)
            alts.extend(_alts)
            if not certp:
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
            if certp:
                break
    # last resort, try to generate a certificate throught our CA
    if not certp:
        fun = get_cert_for
        if selfsigned:
            fun = get_selfsigned_cert_for
        certp, certk = fun(domain, gen=True)
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


def search_matching_selfsigned_certificate(domain, gen=False, as_text=False):
    '''
    Search in the pillar certificate directory the
    certificate belonging to a particular domain
    '''
    if not HAS_SSL:
        raise Exception('Missing pyopenssl')
    certs_dir = get_selfsigned_certs_dir()
    certp, certk = None, None
    # try to get a exact-matching filename<->domain
    if not certp:
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
    # try to see if someone has installed a full certificate containing
    # at least the cert and key but also the auth chain in
    # the well known install dir
    try:
        certp, certk = get_installed_cert_for(domain)
    except CertificateNotFoundError:
        pass
    # last resort, try to generate a certificate throught our CA
    if not certp:
        certp, certk = get_selfsigned_cert_for(domain, gen=gen)
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


def selfsigned_ssl_certs(domains, gen=False, as_text=False):
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
            domain, gen=gen, as_text=as_text)
        if crt_data not in ssl_certs:
            ssl_certs.append(crt_data)
    return ssl_certs


def ssl_certs(domains, **kw):
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
    if isinstance(domains, basestring):
        domains = domains.split(',')
    ssl_certs = []
    for domain in domains:
        crt_data = search_matching_certificate(
            domain, as_text=True)
        if crt_data not in ssl_certs:
            ssl_certs.append(crt_data)
    return ssl_certs


def ca_ssl_certs(domains, **kwargs):
    '''
    Wrapper to ssl_certs to also return the cacert
    information
    Return a triple (ert, key, ca)
    if ca is none: ca==''
    '''
    rdomains = []
    if isinstance(domains, basestring):
        domains = domains.split(',')
    for domain in domains:
        data = ssl_certs(domain, as_text=True)[0]
        cert, chain = ssl_chain(domain, data[0])
        rdomains.append((cert, data[1], chain))
    return rdomains


def common_settings(ttl=60):
    def _do():
        _s,  _g = __salt__, __grains__
        country = _s['grains.get']('defaultlanguage')
        if country:
            country = country[:2].upper()
        else:
            country = 'fr'
        data = _s['mc_utils.defaults'](
            PREFIX, {'country': country,
                     'st': 'Pays de Loire',
                     'l': 'NANTES',
                     'o': 'NANTES',
                     'cn': _g['fqdn'],
                     'email': 'root@' + _g['fqdn'],
                     'domains': [_g['fqdn']],
                     'certificates_domains_map': OrderedDict(),
                     'certificates': OrderedDict()})
        data['domains'] = __salt__['mc_utils.uniquify'](data['domains'])
        return data
    cache_key = 'mc_ssl.common_settings'
    return deepcopy(__salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl))


def reload_settings(data=None):
    if data is None:
        data = common_settings()
    certs = data.pop('certificates', {})
    dcerts = data.setdefault('certificates', OrderedDict())
    matches = data.setdefault('certificates_domains_map', OrderedDict())
    for cert in [a for a in certs]:
        cdata = certs[cert]
        do_chain_load = False
        if len(cdata) < 3:
            do_chain_load = True
        if cdata and not do_chain_load and not cdata[2]:
            if cdata[0].count('BEGIN CERTIFICATE') > 2:
                do_chain_load = True
        if not do_chain_load:
            True
        if do_chain_load:
            chain = ssl_chain(cert, cdata[0])
            key = ssl_key(cdata[1])
            cdata = chain[0], key, chain[1]
        try:
            cert = ssl_infos(cdata[0])['subject'].CN
        except Exception:
            log.error('Error while decoding cert: {0}'.format(cert))
        dcerts[cert] = cdata
        matched_domains = [cert]
        # XXX: load also here subAlNames
        for i in matched_domains + list(data.get('domains', [])):
            match = matches.setdefault(cert, [])
            if cert not in match:
                match.append(cert)
    # be sure to index them by the CN defined in the cert
    for cert in data['certificates']:
        cdata = data['certificates'][cert]
        try:
            cdata[2]
        except Exception:
            raise Exception('Invalid auth chain for {0}'.format(cert))
    return data


def get_configured_cert(domain, gen=False, ttl=60):
    '''
    Return any configured ssl cert for domain or the wildward domain
    matching the precise domain.
    It will prefer to use any real signed certificate over a self
    signed certificate
    '''
    def _do(domain):
        _s,  _g = __salt__, __grains__
        pretendants = []
        if domain == 'localhost':
            domain = _g['fqdn']
        ssettings = reload_settings()
        certs = ssettings['certificates']
        domains = [domain]
        if is_wildcardable(domain):
            wd = '*.' + '.'.join(domain.split('.')[1:])
            domains.append(wd)
        for d in domains:
            data = certs.get(d, None)
            if data:
                pretendants.append(data)
        if not pretendants:
            cert = selfsigned_ssl_certs(domain, gen=gen, as_text=True)[0]
            pretendants.append((cert[0], cert[1], ''))
            certs[domain] = cert[0], cert[1], ''
        pretendants.sort(key=selfsigned_last)
        return pretendants[0]
    cache_key = 'mc_ssl.get_configured_cert{0}'.format(domain)
    return __salt__['mc_utils.memoize_cache'](_do, [domain], {}, cache_key, ttl)


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
        data = reload_settings()
        is_travis = __salt__['mc_nodetypes.is_travis']()
        # even if we make a doublon here, it will be filtered by CN indexing
        for domain in data['domains']:
            if is_travis:
                continue
            data['certificates'][domain] = get_configured_cert(
                domain, gen=True)
        return reload_settings(data)
    return _settings()


def get_cert_infos(domain, ttl=60):
    def _do(domain):
        cdata = get_configured_cert(domain)
        try:
            domain = ssl_infos(cdata[0])['subject'].CN
        except Exception:
            log.error(
                'Error while decoding cert for domain: {0}'.format(domain))
        spath = '/etc/ssl/cloud/separate'
        cpath = '/etc/ssl/cloud/certs'
        return {'domaincert': domain,
                'cert_data': cdata,
                'crt': '{0}/{1}.crt'.format(cpath, domain),
                'bundle': '{0}/{1}-{2}.crt'.format(spath, domain, 'bundle'),
                'full': '{0}/{1}-{2}.crt'.format(spath, domain, 'full'),
                'auth': '{0}/{1}-{2}.crt'.format(spath, domain, 'auth'),
                'authr': '{0}/{1}-{2}.crt'.format(spath, domain, 'authr'),
                'only': '{0}/{1}.crt'.format(spath, domain),
                'key': '{0}/{1}.key'.format(spath, domain)}

    cache_key = 'mc_ssl.get_cert_infos{0}'.format(domain)
    return __salt__['mc_utils.memoize_cache'](_do, [domain], {}, cache_key, ttl)
# vim:set et sts=4 ts=4 tw=80:
