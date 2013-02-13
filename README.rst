SCons Hit 'n Run
================

Runs `SCons <http://scons.org>`_, parses its ``--tree=all`` output and reruns the
build if any of the dependencies change.

Warning: This is a bit of a quick hack. Use at your own peril.

Example
-------

``hitnrun -- -j8`` will run the command ``scons --silent --tree=all -j8``,
rerunning it if any dependencies in the tree change.
