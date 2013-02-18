SCons Hit 'n Run
================

Runs `SCons <http://scons.org>`_, parses its ``--tree=all`` output and reruns the
build if any of the dependencies change.

Installation
------------

Easily installed from PyPI::

  pip install hitnrun

...and you're done!

Example
-------

``hitnrun -- -j8`` will run the command ``scons --silent --tree=all -j8``,
rerunning it if any dependencies in the tree change.
