# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
from ConfigParser import SafeConfigParser

import re
import sys


def system_exit(errcode, message=None):
    if message:
        sys.stderr.write(str(message) + '\n')
    sys.exit(errcode)


def read_mapping_file(mappingfile):
    f = open(mappingfile)
    lines = f.readlines()
    dic_data = {}
    for line in lines:
        if re.match("^[a-zA-Z]", line):
            line = line.replace("\n", "")
            key, val = line.split(": ")
            dic_data[key] = val
    return dic_data


def cfg_init(config_file=None, reinit=False):
    CONFIG = None
    if CONFIG and not reinit:
        return CONFIG
    CONFIG = SafeConfigParser()
    CONFIG.read(config_file)
    return CONFIG


def get_release():
    f = open('/etc/redhat-release')
    lines = f.readlines()
    f.close()
    release = "RHEL-" + str(lines).split(' ')[6].split('.')[0]
    return release
