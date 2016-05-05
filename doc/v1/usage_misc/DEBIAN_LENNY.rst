Journal of installing makina-states old an old uncentralamnaged box
=======================================================================


get a recent git
-----------------------
If you do not have a git >= 1.8::

 apt-get build-dep git-core
 wget https://git-core.googlecode.com/files/git-1.9.0.tar.gz
 tar xzvf git*z
 cd git*
 make configure && ./configure && make
 cd /usr/bin && mkdir oldgit && mv git* oldgit
 cd - && make install


recent  ssl
-----------------
::

    export CFLAGS="-fPIC"
    wget http://www.openssl.org/source/openssl-1.0.1g.tar.gz
    tar xzvf openssl-1.0.1g.tar.gz
    cd openssl-1.0.1g
    ./config --prefix=/usr/local shared && make depend && make && make install && ldconfig
    unset CFLAGS

get a recent python
---------------------
If you do not have a python >= 2.7::

    export CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib"
    apt-get build-dep python2.5
    ln -s /usr/local/ /usr/local/ssl
    wget https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tgz --no-check-certificate
    tar xzvf Python-2.7.6.tgz
    cd Python-2.7.6
    ./configure CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib"  --prefix=/usr/local/ --disable-ipv6  --without-fpectl --enable-shared --enable-unicode=ucs4 && make && make install && ldconfig
    mv -f /usr/local/bin/python /usr/local/bin/python.old
    ldconfig
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python2.7
    /usr/local/bin/easy_install -U virtualenv

ZMQ
-----
If you do not have libzmq >= 4 ::

    wget http://download.zeromq.org/zeromq-4.0.4.tar.gz
    tar xzvf zeromq-4.0.4.tar.gz
    cd zeromq-4.0.4
    ./configure --with-pgm --prefix=/usr/local && make && make install && ldconfig

YAML
------
::

    wget http://pyyaml.org/download/libyaml/yaml-0.1.5.tar.gz
    tar xzvf yaml-0.1.5.tar.gz
    cd yaml-0.1.5
    ./configure --prefix=/usr/local && make && make install && ldconfig


Bootstrap makina-states with care
------------------------------------
::

    cd /srv
    mkdir salt
    cd salt
    git clone git@github.com:makinacorpus/makina-states.git
    cd makina-states
    ./_scripts/boot-salt.sh -b stable -m <MINION_ID>


