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

from datetime import datetime
import io
import json
import logging
from optparse import OptionParser
import os
import re
import socket
import sys
import tempfile
import time

from certutils import certutils
from dateutil.tz import tzutc
from splice.common.connect import BaseConnection
import splice.common.utils

from spacewalk_splice_tool import facts, connect, utils, constants
from spacewalk_splice_tool.sw_client import SpacewalkClient
from spacewalk_splice_tool.katello_connect import KatelloConnection, NotFoundException

_LIBPATH = "/usr/share/rhsm"
# add to the path if need be
if _LIBPATH not in sys.path:
    sys.path.append(_LIBPATH)

from subscription_manager.certdirectory import CertificateDirectory

_LOG = logging.getLogger(__name__)
CONFIG = None

SAT_OWNER_PREFIX = 'satellite-'

class DataTransforms:
    """
    a class for transforming data from one format to another
    """

    def __init__(self):
        # TODO: this should get pulled in from the caller instead of being read twice
        global CONFIG
        CONFIG = utils.cfg_init(config_file=constants.SPLICE_CHECKIN_CONFIG)

    def transform_to_rcs(self, consumer):
        """
        convert a katello consumer into something parsable by RCS
        as a MarketingProductUsage obj
        """
        retval = {}

        if consumer.has_key('checkin_time') and consumer['checkin_time'] is not None:
            retval['splice_server'] = _get_splice_server_uuid()
            retval['checkin_date'] = consumer['checkin_time']
            retval['name'] = consumer['name']
            retval['service_level'] = consumer['serviceLevel']
            retval['hostname'] = consumer['facts']['network.hostname']
            retval['instance_identifier'] = consumer['uuid']
            retval['entitlement_status'] = consumer['entitlement_status']
            retval['organization_id'] = str(consumer['environment']['organization_id'])
            retval['organization_name'] = consumer['owner']['displayName']
            retval['facts'] = transform_facts_to_rcs(consumer['facts'])
            return retval
        else:
            _LOG.debug("system entry for %s has no checkin_time, not loading entry into splice db" % consumer['name'])


    def transform_to_consumers(self, system_details):
        """
        Convert system details to katello consumers. Note that this is an ersatz
        consumer that gets processed again later, you cannot pass this directly
        into katello.
        """
        _LOG.info("Translating system details to katello consumers")
        consumer_list = []
        for details in system_details:
            facts_data = facts.translate_sw_facts_to_subsmgr(details)
            # assume 3.1, so large certs can bind to this consumer
            facts_data['system.certificate_version'] = '3.1'
            facts_data['spacewalk-server-hostname'] = CONFIG.get("spacewalk", "host")

            consumer = dict()
            consumer['id'] = details['server_id']
            consumer['facts'] = facts_data
            consumer['owner'] = details['org_id']
            # katello does not allow leading/trailing whitespace here
            consumer['name'] = details['name'].strip()
            consumer['last_checkin'] = details['last_checkin_time']
            consumer['installed_products'] = details['installed_products']

            consumer_list.append(consumer)
        return consumer_list

    def transform_facts_to_rcs(self, facts):
        # rcs doesn't like the "." in fact names
        rcs_facts = {}

        for f in facts.keys():
            rcs_facts[f.replace('.', '_dot_')] = facts[f]

        return rcs_facts

    def transform_entitlements_to_rcs(self, entitlements):
        rcs_ents = []
        for e in entitlements:
            rcs_ent = {}
            rcs_ent['account'] = e['accountNumber']
            rcs_ent['contract'] = e['contractNumber']
            rcs_ent['product'] = e['productId']
            rcs_ent['quantity'] = e['quantity']
            rcs_ents.append(rcs_ent)

        return rcs_ents
