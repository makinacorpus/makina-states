#!/usr/bin/env python
import os
import argparse
import sys
import shutil
from distutils.version import LooseVersion


BURPDIR = os.environ.get("BURPDIR", "/data/burp")
KEEPCOUNT = int(os.environ.get("KEEPCOUNT", "1"))


def cleanup_backup(pbdir, count=1, skipped=None):
    if not skipped:
        skipped = []
    bdir = os.path.abspath(pbdir)
    if not count:
        print('{0} no keep'.format(bdir))
        return
    if not os.path.exists(bdir):
        print('{0} not exists'.format(bdir))
        return
    if not os.path.isdir(bdir):
        print('{0} not dir'.format(bdir))
        return
    cwd = os.getcwd()
    try:
        os.chdir(bdir)
        print('In:: '+bdir)
        to_deleted = {}
        files = [os.path.join(bdir, a) for a in os.listdir(bdir)]
        skippeds = ['finishing']
        for cskipped in skippeds:
            skipped = os.path.join(bdir, cskipped)
            if skipped in files:
                count += 1
                target = os.path.abspath(os.readlink(skipped))
                print('Skipping {0}'.format(target))
                files.pop(files.index(target))
        for i in files:
            if not os.path.isdir(i):
                continue
            if 'current' in i:
                continue
            if os.path.islink(i):
                continue
            stats = os.stat(i)
            to_deleted[i] = stats.st_mtime
        to_delete = to_deleted.items()
        to_delete.sort(key=lambda x: x[1])
        if len(to_delete) <= count:
            print('Nothing to do ({1}<{0})'.format(len(to_delete), count))
            return
        for i in range(count):
            to_delete.pop()
        for i, mtime in to_delete:
            if not os.path.exists(i):
                continue
            print("deleting {0}".format(i))
            shutil.rmtree(i)
    finally:
        os.chdir(cwd)


def main(argv=None):
    if not argv:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--keep-count', type=int, default=KEEPCOUNT)
    parser.add_argument('--dirs', nargs="+")
    opts = parser.parse_args(argv)
    for d in opts.dirs:
        cleanup_backup(d, count=opts.keep_count)


if __name__ == '__main__':
    main()

# vim:set et sts=4 ts=4 tw=80:
