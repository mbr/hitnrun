#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import re
import subprocess
import time
from Queue import Queue, Empty
from threading import RLock

from logbook import Logger, NullHandler, StderrHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


log = Logger('hitnrun')


TREE_EXP = re.compile(r'^((?:[ |]{2})*)\+-(.*)$')

parser = argparse.ArgumentParser()
parser.add_argument('scons_options', nargs='*')
parser.add_argument('--debug', action='store_true', default=False)
parser.add_argument('--collect-time', type=float, default=0.2)
parser.add_argument('--loop-time', type=int, default=1)


def parse_scons_tree(output):
    # construct node tree
    class Node(object):
        def __init__(self, name):
            self.name = name
            self.children = []

        def __repr__(self):
            return 'Node(%r, %r)' % (self.name, self.children)


    root_nodes = []
    for line in output.split('\n'):
        m = TREE_EXP.match(line)
        if not m:
            continue

        level, src = len(m.group(1))/2, m.group(2)

        if level == 0:
            root = Node(src)
            stack = [root]
            root_nodes.append(root)
            plevel = level
            continue

        # not a root node
        if level == plevel+1:
            stack.append(Node(src))
        # sibling
        elif level == plevel:
            stack[-1] = Node(src)
        elif level < plevel:
            stack = stack[:level]
            stack.append(Node(src))
        else:
            raise RuntimeError('Bad tree')

        stack[-2].children.append(stack[-1])
        plevel = level

    return root_nodes


class QueueingHandler(FileSystemEventHandler):
    def __init__(self, files=set([])):
        self.q = Queue()

        self._files_lock = RLock()
        self._files = files

    def on_any_event(self, event):
        with self._files_lock:
            if not self._files:
                log.debug('Watching all files (no valid tree): %s' %
                        event.src_path)
            elif not event.src_path in self._files:
                log.debug('Skipping %s, not in tree' % event.src_path)
                return

        self.q.put(os.path.abspath(event.src_path))

    @property
    def files(self):
        raise RuntimeError('Cannot get files')

    @files.setter
    def files(self, value):
        with self._files_lock:
            self._files = value


def run_scons_and_parse_tree(scons_cmd):
    env = os.environ.copy()
    env['TERM'] = 'vt100'

    log.info(' '.join(scons_cmd))
    output = subprocess.check_output(scons_cmd, env=env)

    # collect file leaves
    files = []
    for root in parse_scons_tree(output):
        stack = [root]

        while stack:
            node = stack.pop()

            if not node.children:
                files.append(node.name)
            else:
                stack.extend(node.children)

    rv = set(files)
    log.debug('Fileset now %r' % (rv,))
    return rv


def interruptable_get(q, timeout):
    while True:
        try:
            return q.get(True, timeout)
        except Empty:
            continue


def collect_from(q, timeout):
    results = []

    while True:
        try:
            results.append(q.get(True, timeout))
        except Empty:
            return results


def main():
    args = parser.parse_args()
    NullHandler().push_application()
    StderrHandler(level='DEBUG' if args.debug else 'INFO').push_application()

    sconsfile_path = '.'

    event_handler = QueueingHandler()

    observer = Observer()
    observer.schedule(event_handler, path=sconsfile_path, recursive=True)
    observer.start()

    try:
        while True:
            # run scons
            scons_cmd = ['scons', '-s', '--tree=all'] + args.scons_options
            try:
                files = run_scons_and_parse_tree(scons_cmd)
            except subprocess.CalledProcessError, e:
                log.warning('Error running scons: %s' % e)
            else:
                event_handler.files = set(
                    [os.path.abspath(fn) for fn in files]
                )

            # wait for next event or C-c
            src = interruptable_get(event_handler.q, args.loop_time)
            log.info('Change in %s, waiting for more changes...' % src)
            results = collect_from(event_handler.q, args.collect_time)
            log.info('%d more changes' % len(results))
    except KeyboardInterrupt:
        print "Stopping observer..."
        observer.stop()
        observer.join()
