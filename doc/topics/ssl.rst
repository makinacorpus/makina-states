Manage ssl certificates
========================
General use
---------------
Management is done via the pillar, and via the
**makina-states.localsettings.ssl** sls.

After configuration, apply it to your system via::

    bin/salt-call -l all state.sls makina-states.localsettings.ssl

Or via ansible (remote host)::

    ANSIBLE_TARGETS="$hostname" bin/ansible-playbook \
        ansible/plays/saltcall.yml -e saltargs makina-states.localsettings.ssl

Add a certificate to the system trust system (add a 'ca')
----------------------------------------------------------a

pillar/pillar.d/cert.sls::

    #                                   <CN>
    makina-states.localsettings.ssl.cas.foobar: |
      -----BEGIN CERTIFICATE-----
      MIIDejCCAmKgAwIBAgICA+gwDQYJKoZIhvcNAQELBQAwfzELMAkGA1UEBhMCRlIx
      DDAKBgNVBAgMA1BkTDEPMA0GA1UEBwwGTmFudGVzMRYwFAYDVQQKDA1NYWtpbmEg
      Q29ycHVzMQ8wDQYDVQQDDAZmb29iYXIxKDAmBgkqhkiG9w0BCQEWGWNvbnRhY3RA
      bWFraW5hLWNvcnB1cy5jb20wIBcNMTYwNTA0MTA0NjAzWhgPMzAzNDExMDQxMDQ2
      MDNaMH8xCzAJBgNVBAYTAkZSMQwwCgYDVQQIDANQZEwxDzANBgNVBAcMBk5hbnRl
      czEWMBQGA1UECgwNTWFraW5hIENvcnB1czEPMA0GA1UEAwwGZm9vYmFyMSgwJgYJ
      KoZIhvcNAQkBFhljb250YWN0QG1ha2luYS1jb3JwdXMuY29tMIIBIjANBgkqhkiG
      9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnLYWB4f9lRVc/fbqOvOCNTCefWnNwKehyf9z
      LKzZ93ki5bHYLKUoI7tWK2UOKNbnADhEfgGiWNcGtdrr9wc4FFLFR43tUfIxMfqe
      wUcsv06V9IsmIP4Pi+knAPZG5fXystlPfLjom4bCx5mQr2SGIijw2ogYHKAIdgZJ
      rviDWM2XIbdEx0TIqkOAokKqUtDr8ZEG289P5v5mrHjacAC8GzhxCgg1RWmaJOhW
      jc6bfdgLEOQCwt3hE92r+qrh0JjxBINVLE6IO8dL1jGxN8O+U/sQdhDvuN1bwyXd
      8117+FSP8C+nnOK37MI27qv0D+sEZXZXAdEAY6w0WF4EAuY/kwIDAQABMA0GCSqG
      SIb3DQEBCwUAA4IBAQBHG6MkNhaeXWqMqzcYmLWZQZ6hONfRaK7lZlKmly6yVzLJ
      Y6v5wPMtWDzE0ALS0K2nhG4dEuEo1D1/dQhdz+zmJC5+xVnCzzWIxfNs0GgQMTVj
      eEmp3Hl0QBwe66swFaMKPz9+1eiQKaTE4pcwOXGEFwephaJWkswX4Fw0o9CA7NLl
      z0uIpHB12tcGlxS7joraj6aV4nKj+T3xVzsQqR2x5jbZMzsn/1W4afeSKZkBWiNI
      Z1cASST8OvDiBkQna7LNqDVfogezK0h/8Wbqp5dipeNIY9xu/L4Hr9+Djb9mOwp+
      gKtKM4seNltkeKgYrupAUecK3Rs+xiF9j5xiv2X1
      -----END CERTIFICATE-----


Add a certificate and it's key for reuse in makina-states packages applications
------------------------------------------------------------------------------------
pillar/pillar.d/cert.sls::

    #                                            <CN>
    makina-states.localsettings.ssl.certificates.titi:
     - |
       -----BEGIN CERTIFICATE-----
       MIIDdjCCAl6gAwIBAgICA+gwDQYJKoZIhvcNAQELBQAwfTELMAkGA1UEBhMCRlIx
       DDAKBgNVBAgMA1BkTDEPMA0GA1UEBwwGTmFudGVzMRYwFAYDVQQKDA1NYWtpbmEg
       Q29ycHVzMQ0wCwYDVQQDDAR0aXRpMSgwJgYJKoZIhvcNAQkBFhljb250YWN0QG1h
       a2luYS1jb3JwdXMuY29tMCAXDTE2MDUwNDExMDcxNFoYDzMwMzQxMTA0MTEwNzE0
       WjB9MQswCQYDVQQGEwJGUjEMMAoGA1UECAwDUGRMMQ8wDQYDVQQHDAZOYW50ZXMx
       FjAUBgNVBAoMDU1ha2luYSBDb3JwdXMxDTALBgNVBAMMBHRpdGkxKDAmBgkqhkiG
       9w0BCQEWGWNvbnRhY3RAbWFraW5hLWNvcnB1cy5jb20wggEiMA0GCSqGSIb3DQEB
       AQUAA4IBDwAwggEKAoIBAQDMRnNmGHdSfjmv/HQSLKQ0aIhukNQJP1/pVYfoHN/X
       BE5pbbM3voZaecq5puJV1CAojYO9XkIY6FFOQnXbr+285ectuTHFHGTQpw/cEtUd
       uHR7SXdhcfFOMw2og/WcdiOj5+WqEkm5hsT5QWMFTYQxXsRtwWVxx9JzBSStPpzi
       aJ1bfg51F+iEFvnkAsYN6++CAGp93pKNhKKyPx52fiiSwVH5+7Iouw5BzX68DQK5
       1i2YoHDRKdZmBJ/wVUgISsuHEf4JhKMfyiQWvfjqNL5FQx4nEnhHbcrYr+/h/2+A
       7IdscdbpQa4mKK6+5B9EIjR/c/6LKmXhaQuNwg+UaP9JAgMBAAEwDQYJKoZIhvcN
       AQELBQADggEBAB/egp+ifuMfl7tFiRiO95QeIu6YLNSs6l2ZQ8uHSqlQ6/8GSq/J
       C1vt/yy4nPZ/14AonlIxWiKMH/1I96Y7W/8KZ5v9DbYsjGwO1TwqNxsqxjjMlW4g
       Qb1L4vnAq+25HhX0M1xiJWErgPfzMCVTyOhhuVaIPVTZUBhN5GsVtzuzeC4Vpg1O
       wAhBRgbyi9gxdWoxeaujColAoiwBYgLt6d+jg7I7RSYvd6bIixc00G0J4zY0d8jB
       ztK3UXbf4G0Bt7R/DcyZ0Tsp51+d5vpD+UjKkpijwhDkUGNC1ljD5M95NlmbCPdp
       5ODKbWRuHLcUyzEAjzplwC6FpAlvN11SanA=
       -----END CERTIFICATE-----
     - |
       -----BEGIN PRIVATE KEY-----
       MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDMRnNmGHdSfjmv
       /HQSLKQ0aIhukNQJP1/pVYfoHN/XBE5pbbM3voZaecq5puJV1CAojYO9XkIY6FFO
       QnXbr+285ectuTHFHGTQpw/cEtUduHR7SXdhcfFOMw2og/WcdiOj5+WqEkm5hsT5
       QWMFTYQxXsRtwWVxx9JzBSStPpziaJ1bfg51F+iEFvnkAsYN6++CAGp93pKNhKKy
       Px52fiiSwVH5+7Iouw5BzX68DQK51i2YoHDRKdZmBJ/wVUgISsuHEf4JhKMfyiQW
       vfjqNL5FQx4nEnhHbcrYr+/h/2+A7IdscdbpQa4mKK6+5B9EIjR/c/6LKmXhaQuN
       wg+UaP9JAgMBAAECggEAPkn9RlSPjggPbyp7+k7Cg3icoZpoDanVhUEfgBfN6bLW
       di+NRqJCNbSNrK7GtYVJiRQd59CmNxIgOMzrQ2ISDFfOdpLSKljOJRHMND9J3RYx
       7qYoUP59pmrK72fNrTgZBhHgZkvNT1VZGuhlWWiZtrQ/EXi3hkp4UbpvxKQjEqZn
       o2+vbUYh440dKdw+iJnDAYZi/1yFCqiIxkWUSFFky8gjppQ7CBeQ4LEHKPodd4A2
       ccnK8op6H5n26Xqdi65G0SR+X39xtEGp8pzUQW8XaXCjEtBNhD95ymGXEmq8KfqG
       XcN6nBMVp5V9X4+xFg2hBsFPsL6xrT7deASBKyDQAQKBgQD9VG8okA1rd11ttyvi
       DhIV6PlYBxhEex4lGeqOrjETKMsAFDsJ5Ntlr3MiXiLIuQ0pAcu3tpxNEkTLkcHo
       e0VpP7HCr14vnCpZyB1B8wTmbBJVMXkD+oaN7pzEJhauaombfDRH4NKd87lgveLG
       3x/CFHdJfEvxwjRdpER+ZxJvIQKBgQDObaa9WcyZnuB7R109TTiZgSGo1XljF1m9
       Ji+85sSdV1mHnUyghgszbnW5s8dM1sweY5ZAONFsF9j06iL2h1XnGlgKHBL22UGH
       o5nc5/oHfuc/YmRdSUCgmwSZixrInFjfvUiE/tR/j4z2AnpEB4/8genEm+elXYIE
       uodJpj3TKQKBgQChY+FNXjiudmU3OLLkWUJ8Yug3hI2ZUzZpPJGKRL9PDXYGntzd
       +MctiRE4m/BdIEeaEGLQr630C+d4KWv3yFD4NHPzK/Y9LqhsemjpUwGUKtWjINmQ
       B1MhqRqGfB2HEKiKPh6wjDKiHlvDnjWTrSJ2asN0NZPMeYUTA0v/m3rLAQKBgFJZ
       K8sdp6Eg4CxNq8RoqcuS1/qiLmp5RjNOqHyTEpwx3GVdOtROpOk/h3ctYLQmfAcj
       cyzrfZ/BY6tQO+Jc2sf2mmhuCqKuyJVzjk2xvOyAk3+VoLQWJNHtBUi7VVPyCwI2
       YFet0NeSTIlXM68v1SDGMptcFmzBgLyiLJYU21UBAoGBAIhSvpsw3z/gAf9nbciZ
       9puJiPqFBld7DrCp69iaD/ryXzLfzwI3bzWR8M8TuBO6DxApiYx7Zps4QabPQZTN
       U4UFg0AcdRh27OUXYtGENw7W0ssZKhlII78WB+0haAwe+kQJ4aNpF0eqWXLH7thR
       zKKdzi+lMlG5NimeR246wBvX
       -----END PRIVATE KEY-----


Add certificates via the makina-states ext_pillar
-------------------------------------------------
When using mc_pillar deployment, edit your local **etc/makina-states/database.sls**

Take an example on the `database.sls <https://github.com/makinacorpus/makina-states/blob/v2/etc/makina-states/database.sls.in>`_ ssl section.

You can add either certificates for a host by specifying them by the **id** index or
configure infra wide certs by setting them in the **default** section.

Reconfigure the SSL system
----------------------------
::

    bin/salt-call -lall state.sls makina-states.localsettings.ssl

Use the ssl macro in a state to register a certificate
---------------------------------------------------------

This add the certificate inside the cloud ssl directories
Then also may add it to the systemwide ssl trust

foo.sls::

    {% import "makina-states/localsettings/ssl/macros.jinja" as ssl with context %}
    {{ ssl.install_certificate(
            cert_string
            [, [cert_key_string]]
            [, trust=True/False]]
    )}}

Parameters:

    cert_string
        either a certificate string (full certificate in PEM format)
        or a path to load a certificate in PEM format
        or a key inside the mc_ssl.settings.certificates regitry

    cert_key_string (optional)
        in case of cert_string is neither a certificate inline or a certificate
        filepath, this will lookup inside the pillar for a matching certificate
        inside the mc_ssl.settings.certificates key.

    trust (optional)
        boolean to tell to register the certificate to the
        system-wide ssl trusted certe
