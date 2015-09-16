CouchApp: Standalone CouchDB Application Development Made Simple
================================================================
.. image:: https://img.shields.io/travis/couchapp/couchapp/master.png?style=flat-square
   :target: https://travis-ci.org/couchapp/couchapp

.. image:: https://img.shields.io/coveralls/couchapp/couchapp/master.png?style=flat-square
   :target: https://coveralls.io/r/couchapp/couchapp

CouchApp is designed to structure standalone CouchDB application
development for maximum application portability.

CouchApp is a set of scripts and a `jQuery <http://jquery.com>`_ plugin
designed  to bring clarity and order to the freedom of
`CouchDB <http://couchdb.apache.org>`_'s document-based approach.

Also, be sure to checkout our Erlang-based sibling,
`erica <https://github.com/benoitc/erica>`_.

Write apps using just JavaScript and HTML
-----------------------------------------

Render HTML documents using JavaScript templates run by CouchDB. You'll
get parallelism and cacheability, **using only HTML and JS.** Building
standalone CouchDB applications according to correct principles affords
you options not found on other platforms.

Deploy your apps to the client
++++++++++++++++++++++++++++++

CouchDB's replication means that programs running locally can still be
social. Applications control replication data-flows, so publishing
messages and subscribing to other people is easy. Your users will see
the benefits of the web without the hassle of requiring always-on
connectivity.

Installation
------------

Couchapp requires Python 2.7. Couchapp is most easily installed
using the latest versions of the standard python packaging tools, setuptools 
and pip. They may be installed like so::

    $ curl -O https://bootstrap.pypa.io/get-pip.py
    $ sudo python get-pip.py

Installing couchapp is then simply a matter of::

    $ pip install couchapp

On OSX 10.6/10.7 you may need to set ARCH_FLAGS::

    $ env ARCHFLAGS="-arch i386 -arch x86_64" pip install couchapp

To install/upgrade a development version of couchapp::

    $ pip install -e git+http://github.com/couchapp/couchapp.git#egg=Couchapp

Note: Some installations need to use *sudo* command before each command
line.

Note: On debian system don't forget to install python-dev.

To install on Windows follow instructions `here
<https://couchapp.readthedocs.org/en/latest/couchapp/install.html#installing-on-windows>`_.

More installation options on the `website
<https://couchapp.readthedocs.org/en/latest/couchapp/install.html>`_.

Getting started
---------------

Read the `tutorial <https://couchapp.readthedocs.org/en/latest/couchapp/gettingstarted.html>`_.

Documentation
-------------

It's available at https://couchapp.readthedocs.org/en/latest

Testing
-------

We use `nose <http://nose.readthedocs.org/>`_. and
`nose-testconfig <https://pypi.python.org/pypi/nose-testconfig>`_. for setting
up and running tests.

In the ``tests`` directory, copy ``config.sample.ini`` to ``config.ini``, tweak
the settings, and then run the tests from the main ``couchapp`` directory (as
the paths below are relative to that)::

    $ nosetests --tc-file=tests/config.ini

If you're wanting to generate code coverage reports (because you've got big
plans to make our tests better!), you can do so with this command instead::

    $ nosetests --with-coverage --cover-package=couchapp --cover-html --tc-file=tests/config.ini

Thanks for testing ``couchapp``!

Building the docs
-----------------

We generate the document via ``sphinx``.

First, prepare our building env.
We need ``sphinx``::

    $ cd docs/
    $ pip install sphinx

To build it, just issue::

    $ make html

And sphinx will generate static html at *docs/_build/html*.
We can browse the site from this dir already.

Other resources
---------------

* `List of CouchApps <https://couchapp.readthedocs.org/en/latest/user/list-of-couchapps.html>`_
