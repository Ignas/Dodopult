APP_NAME = 'Dodopult'


cfg = {
    'name': APP_NAME,
    'version': '1.0dev',
    'description': 'A simple game',
    'author': 'Ignas Mikalajunas and Marius Gedminas',
    'author_email': '',
    'url': '',

    'py2exe.target': '',
    'py2exe.icon': 'assets\\Dodo.ico', #64x64
    'py2exe.binary': APP_NAME, #leave off the .exe, it will be added
    }

# usage: python setup.py command
#
# sdist - build a source dist
# py2exe - build an exe
#
# the goods are placed in the dist dir for you to .zip up or whatever...

from distutils.core import setup, Extension
try:
    import py2exe
except:
    pass

import sys
import glob
import os
import shutil

try:
    cmd = sys.argv[1]
except IndexError:
    raise SystemExit('Usage: setup.py py2exe')

# utility for adding subdirectories
def add_files(dest, generator):
    for dirpath, dirnames, filenames in generator:
        for name in 'CVS', '.svn', '.git':
            if name in dirnames:
                dirnames.remove(name)

        for name in filenames:
            if '~' in name: continue
            suffix = os.path.splitext(name)[1]
            if suffix in ('.pyc', '.pyo'): continue
            if name[0] == '.': continue
            filename = os.path.join(dirpath, name)
            dest.append(filename)

# define what is our data
data = []
add_files(data, os.walk('assets'))
print data
data.extend(glob.glob('*.txt'))
data.extend(glob.glob('*.png'))
# define what is our source
src = []
add_files(src, os.walk('lib'))
src.extend(glob.glob('*.py'))

# build the sdist target
if cmd == 'sdist':
    f = open("MANIFEST.in", "w")
    for l in data: f.write("include "+l+"\n")
    for l in src: f.write("include "+l+"\n")
    f.close()

    setup(
        name=cfg['name'],
        version=cfg['version'],
        description=cfg['description'],
        author=cfg['author'],
        author_email=cfg['author_email'],
        url=cfg['url'],
        )

# build the py2exe target
if cmd in ('py2exe',):
    dist_dir = os.path.join('dist', cfg['py2exe.target'])
    data_dir = dist_dir

    src = 'dodo.py'
    dest = cfg['py2exe.binary']+'.py'
    shutil.copy(src, dest)

    setup(
        options={'py2exe': {
            'dist_dir': dist_dir,
            'dll_excludes': ['_dotblas.pyd', '_numpy.pyd']
            }},
        windows=[{
            'script': dest,
            'icon_resources': [(0, 'assets\\Dodo.ico')],
            }],
        )

# recursively make a bunch of folders
def make_dirs(dname_):
    parts = list(os.path.split(dname_))
    dname = None
    while len(parts):
        if dname == None:
            dname = parts.pop(0)
        else:
            dname = os.path.join(dname, parts.pop(0))
        if not os.path.isdir(dname):
            os.mkdir(dname)

# copy data into the binaries 
if cmd in ('py2exe',):
    dest = data_dir
    for fname in data:
        dname = os.path.join(dest, os.path.dirname(fname))
        make_dirs(dname)
        if not os.path.isdir(fname):
            shutil.copy(fname, dname)
