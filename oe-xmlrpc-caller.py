#!/usr/bin/env python2

import sys
import os
import re
from pprint import pprint, pformat
import argparse
import xmlrpclib

re_autoeval = re.compile(r"^(\d+|\[.*\]|\{.*\}|\".*\"|'.*')$")

def warn(*messages):
    sys.stderr.write(" ".join(map(unicode, messages))+"\n")

def die(*messages):
    warn(*messages)
    sys.exit(1)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--help', action='store_true')
parser.add_argument('--url')
parser.add_argument('--uid')
parser.add_argument('--login', '--username', '-U', default='admin')
parser.add_argument('--password', '-W', type=str, default=None)
parser.add_argument('--host', '-h', default='localhost')
parser.add_argument('--port', '-p', type=int)
parser.add_argument('--protocol', default='http')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--pipe', action='store_true')
parser.add_argument('--pretty', action='store_true')
parser.add_argument('db', metavar='database')
parser.add_argument('model', nargs='?')
parser.add_argument('method', nargs='?')
parser.add_argument('args', nargs='*')
opt = parser.parse_args()

if opt.help:
    parser.print_help()
    sys.exit(0)

def debug(*messages):
    if opt.debug:
        warn("debug:", *messages)

def require(args):
    for arg in (args.split()
              if isinstance(args, basestring)
              else args):
        if not getattr(opt, arg):
            die("missing argument:", arg)

if not opt.port:
    if opt.protocol == 'http':
        opt.port = 8069
    elif opt.protocol == 'https':
        opt.port = 8071
    else:
        die("can not determine port for protocol:", opt.protocol)
    debug("port determinated is:", opt.port)

if not opt.url:
    require("protocol host port")
    opt.url = "%s://%s:%s/xmlrpc" % (opt.protocol, opt.host, opt.port)
    debug("url determinated is:", opt.url)

if not opt.password:
    opt.password = opt.login

if not opt.uid:
    require("url login password")
    opt.uid = xmlrpclib.ServerProxy(opt.url + '/common')\
        .login(opt.db, opt.login, opt.password)
    if not opt.uid:
        die("login failed:", "%s@%s" % (opt.login, opt.db),
            "(password: %s)" % opt.password)
    elif not opt.model:
        print "login success:", "%s@%s" % (opt.login, opt.db), \
            "(password: %s, uid=%s)" % (opt.password, opt.uid)
        sys.exit(0)
    debug("login uid is:", opt.uid)

require("url db uid password model method")

opt.args = [
    (eval(arg) if re_autoeval.match(arg) else arg)
    for arg in opt.args ]

debug("call", opt.method, "on model", opt.model)
debug("arguments are:", pformat(opt.args))

result = xmlrpclib.ServerProxy(opt.url + '/object')\
    .execute(opt.db, opt.uid, opt.password, opt.model, opt.method, *opt.args)

if (os.isatty(sys.stdout.fileno()) or opt.pretty) and not opt.pipe:
    debug("pretty print")
    pprint(result)
else:
    debug("pipable print")
    print result
