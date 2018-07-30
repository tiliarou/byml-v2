#!/usr/bin/env python3
import argparse
import io
import os
import re
import shutil
import sys
import yaml

from . import byml
from . import yaz0_util

def byml_to_yml() -> None:
    parser = argparse.ArgumentParser(description='Converts a BYML file to YAML.')
    parser.add_argument('byml', help='Path to a BYML file', nargs='?', default='-')
    parser.add_argument('yml', help='Path to destination YAML file', nargs='?', default='-')
    args = parser.parse_args()

    dumper = yaml.CDumper
    yaml.add_representer(byml.Int, lambda d, data: d.represent_int(data), Dumper=dumper)
    yaml.add_representer(byml.Float, lambda d, data: d.represent_float(data), Dumper=dumper)
    yaml.add_representer(byml.UInt, lambda d, data: d.represent_scalar(u'!u', '0x%08x' % data), Dumper=dumper)
    yaml.add_representer(byml.Int64, lambda d, data: d.represent_scalar(u'!l', str(data)), Dumper=dumper)
    yaml.add_representer(byml.UInt64, lambda d, data: d.represent_scalar(u'!ul', str(data)), Dumper=dumper)
    yaml.add_representer(byml.Double, lambda d, data: d.represent_scalar(u'!f64', str(data)), Dumper=dumper)

    file = sys.stdin.buffer if args.byml == '-' else open(args.byml, 'rb')
    with file:
        data = file.read()
        if data[0:4] == b'Yaz0':
            data = yaz0_util.decompress(data)
        root = byml.Byml(data).parse()

        if args.byml != '-':
            args.yml = args.yml.replace('!!', os.path.splitext(args.byml)[0])
        elif '!!' in args.yml:
            sys.stderr.write('error: cannot use !! (for input filename) when reading from stdin\n')
            sys.exit(1)
        output = sys.stdout if args.yml == '-' else open(args.yml, 'w')
        with output:
            yaml.dump(root, output, Dumper=dumper, allow_unicode=True)

def yml_to_byml() -> None:
    parser = argparse.ArgumentParser(description='Converts a YAML file to BYML.')
    parser.add_argument('yml', help='Path to a YAML file', nargs='?', default='-')
    parser.add_argument('byml', help='Path to destination BYAML file', nargs='?', default='-')
    parser.add_argument('-V', '--version', default=2, help='BYML version (1, 2, 3)')
    parser.add_argument('-b', '--be', action='store_true', help='Use big endian. Defaults to false.')
    args = parser.parse_args()

    loader = yaml.CSafeLoader
    yaml.add_constructor(u'tag:yaml.org,2002:int', lambda l, node: byml.Int(l.construct_yaml_int(node)), Loader=loader)
    yaml.add_constructor(u'tag:yaml.org,2002:float', lambda l, node: byml.Float(l.construct_yaml_float(node)), Loader=loader)
    yaml.add_constructor(u'!u', lambda l, node: byml.UInt(l.construct_yaml_int(node)), Loader=loader)
    yaml.add_constructor(u'!l', lambda l, node: byml.Int64(l.construct_yaml_int(node)), Loader=loader)
    yaml.add_constructor(u'!ul', lambda l, node: byml.UInt64(l.construct_yaml_int(node)), Loader=loader)
    yaml.add_constructor(u'!f64', lambda l, node: byml.Double(l.construct_yaml_float(node)), Loader=loader)

    file = sys.stdin if args.yml == '-' else open(args.yml, 'r', encoding='utf-8')
    with file:
        root = yaml.load(file, Loader=loader)
        buf = io.BytesIO()
        byml.Writer(root, be=args.be, version=args.version).write(buf)
        buf.seek(0)

        if args.yml != '-':
            args.byml = args.byml.replace('!!', os.path.splitext(args.yml)[0])
        elif '!!' in args.byml:
            sys.stderr.write('error: cannot use !! (for input filename) when reading from stdin\n')
            sys.exit(1)

        if args.byml != '-':
            extension = os.path.splitext(args.byml)[1]
            if extension.startswith('.s'):
                buf = io.BytesIO(yaz0_util.compress(buf.read()))

        output = sys.stdout.buffer if args.byml == '-' else open(args.byml, 'wb')
        with output:
            shutil.copyfileobj(buf, output)