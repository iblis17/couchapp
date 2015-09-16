.. _install:

Installation
============

The newest install instructions are always in the
`README <https://github.com/couchapp/couchapp/blob/master/README.rst>`__


Requirements
------------

-  Python 2.7 (Python 3.x will be supported soon)
-  the header files of the Python version that is used, which are
   included e.g. in the according development package ``python-dev``
   (may have a different name depending on your system)


Installing on all UNIXs
-----------------------

To install couchapp using ``easy_install`` you must make sure you have a
recent version of distribute installed:

::

    $ curl -O http://python-distribute.org/distribute_setup.py
    $ sudo python distribute_setup.py
    $ sudo easy_install pip

To install or upgrade to the latest released version of couchapp:

::

    $ sudo pip install couchapp
    $ sudo pip install --upgrade couchapp

To install/upgrade development version:

::

    $ sudo pip install git+http://github.com/couchapp/couchapp.git#egg=Couchapp


Installing in a sandboxed environnement
---------------------------------------

If you want to work in a sandboxed environnement which is recommended if
you don't want to not *pollute* your system, you can use
`virtualenv <http://pypi.python.org/pypi/virtualenv>`_ :

::

    $ curl -O http://python-distribute.org/distribute_setup.py
    $ sudo python distribute_setup.py
    $ easy_install pip
    $ pip install virtualenv

Then to install couchapp :

::

    $ pip -E couchapp_env install couchapp

This command create a sandboxed environment in ``couchapp_env`` folder.
To activate and work in this environment:

::

    $ cd couchapp_env && . ./bin/activate

Then you can work on your couchapps. I usually have a ``couchapps``
folder in ``couchapp_env`` where I put my couchapps.


Installing on Mac OS X
----------------------

.. warning::
    This section is out-of-date.
    We need you help for testing on newer OSX with newer ``couchapp.py``


Using CouchApp Standalone executable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download
`Couchapp-0.8.1-macosx.zip <https://github.com/downloads/couchapp/couchapp/couchapp-0.8.1-macosx.zip>`__
on `Github <http://github.com/>`__ then double-click on the installer.

Using the Python metapackage for Mac OS X 10.5 or Mac OS X 10.6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `couchapp-1.0.0-macosx.zip <https://github.com/downloads/couchapp/couchapp/couchapp-1.0.0-macosx.zip>`_
   

Using Homebrew
~~~~~~~~~~~~~~

To install easily couchapp on Mac OS X, it may be easier to use
`Homebrew <http://github.com/mxcl/homebrewbrew>`_ to install ``pip``.

Once you `installed
Homebrew <http://wiki.github.com/mxcl/homebrew/installation>`_, do:

::

    $ brew install pip
    $ env ARCHFLAGS="-arch i386 -arch x86_64" pip install couchapp


Installing on Ubuntu
--------------------

.. warning::

    Our PPA is out-of-date.
    We need your help for upgrading the packages.

If you use `Ubuntu <http://www.ubuntu.com/>`_, you can update your
system with packages from our PPA by adding ``ppa:couchapp/couchapp`` to
your system's Software Sources.

Follow **instructions**
`here <https://launchpad.net/~couchapp/+archive/couchapp>`_.


Installing on Windows
---------------------

.. warning::

    Standalone executable is out-of-date.
    We need your help for testing and buinding newer ``couchapp.py``

There are currently 2 methods to install on windows:

-  `Standalone Executable
   1.0.0 <https://github.com/downloads/couchapp/couchapp/couchapp-1.0.0-win.zip>`_
   Does not require Python
-  `Python installer for Python 2.7 <windows-python-installers.md>`_
   Requires Python

In case the above is not updated, check out the `downloads
section <https://github.com/couchapp/couchapp/downloads>`_ in GitHub
