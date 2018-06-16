#!/usr/bin/env python3
import re
import sys
import yaml

import byml

if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help']:
    sys.stderr.write("Usage: byml_to_yml.py <BYML>")
    sys.exit(1)

dumper = yaml.CDumper
yaml.add_representer(byml.Int, lambda d, data: d.represent_int(data), Dumper=dumper)
yaml.add_representer(byml.Float, lambda d, data: d.represent_float(data), Dumper=dumper)
yaml.add_representer(byml.UInt, lambda d, data: d.represent_scalar(u'!u', '0x%08x' % data), Dumper=dumper)
yaml.add_representer(byml.Int64, lambda d, data: d.represent_scalar(u'!l', str(data)), Dumper=dumper)
yaml.add_representer(byml.UInt64, lambda d, data: d.represent_scalar(u'!ul', str(data)), Dumper=dumper)
yaml.add_representer(byml.Double, lambda d, data: d.represent_scalar(u'!f64', str(data)), Dumper=dumper)

if sys.argv[1] == '-':
    f = sys.stdin.buffer
else:
    f = open(sys.argv[1], "rb")

with f as file:
    data = file.read()
    root = byml.Byml(data).parse()
    yaml.dump(root, sys.stdout, Dumper=dumper, allow_unicode=True)
