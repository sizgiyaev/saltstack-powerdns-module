# -*- coding: utf-8 -*-
'''
Module to provide access to the PowerDNS Authoritative Server API

:configuration: This module uses the requests python library::

'''

import logging
import json

from salt.ext.six import string_types
from salt.exceptions import get_error_message as _get_error_message

__virtualname__ = 'powerdns'

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

log = logging.getLogger(__name__)

def __virtual__():
    '''
    Only load this module if requests is installed
    '''

    if HAS_REQUESTS:
        return __virtualname__
    else:
        return (False, 'The powerdns execution module cannot be loaded: the requests library is not available.')


class PowerDNSError(Exception):
    def __init__(self, url, status_code, message):
        self.url = url
        self.status_code = status_code
        self.message = message
        super(PowerDNSError, self).__init__('Request URL: {url}, Response code: {status_code}, Message: {message}'.format(**locals()))


class PowerDNSClient:
    def __init__(self):
        self.url = __salt__['config.option']('powerdns.url') + '/api/v1'
        self.server = __salt__['config.option']('powerdns.server')
        self.headers = {'X-API-Key': __salt__['config.option']('powerdns.api_key'),
                        'content-type': 'application/json',
                        'accept': 'application/json'
                        }
        self.verify = __salt__['config.option']('powerdns.veirfy')

    def handle_request(self, req):
        if req.status_code in [200, 201, 204]:
            if req.text:
                try:
                    return json.loads(req.text)
                except Exception as e:
                    print(e) # same as yield
            return True
        elif req.status_code == 404:
            error_message = 'Not found'
        elif req.status_code == 422:
            error_message = json.loads(req.text)['error']
        else:
            error_message = self._get_request_error_message(data=req)

        raise PowerDNSError(url=req.url,
                            status_code=req.status_code,
                            message=error_message)


    def _get_request_error_message(self, data):
        request_json = data.json()
        if 'error' in request_json:
            request_error = request_json.get('error')
        elif 'errors' in request_json:
            request_error = request_json.get('errors')
        else:
            request_error = 'No error message found'
        return request_error
    
    def get_zones_url(self):
        return '{url}/servers/{server}/zones'.format(url=self.url, server=self.server)

    def get_zone_url(self, name):
        return '{url}/{name}'.format(url=self.get_zones_url(), name=name)


def list_zones():
    client = PowerDNSClient()
    try:
        req = requests.get(url=client.get_zones_url(), headers=client.headers, verify=client.verify)
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to get list of zones: %s" % (e))
        return {}
    
    return [zone['name'] for zone in ret]

def get_zone(name):
    client = PowerDNSClient()

    try:
        req = requests.get(url=client.get_zone_url(name), headers=client.headers, verify=client.verify)
        if req.status_code == 422: # If zone doesn't exist
            return {}
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to get zone info: %s" % (e))
        return {}

    return ret

def zone_exists(name):
    if get_zone(name):
        return True
    return False

def add_zone(name, data={}):
    client = PowerDNSClient()

    data['name'] = name
    if 'kind' not in data.keys():
        data['kind'] = ''
    if 'nameservers' not in data.keys():
        data['nameservers'] = []
    
    try:
        req = requests.post(url=client.get_zones_url(), data=json.dumps(data), headers=client.headers, verify=client.verify)
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to add zone: '%s'" % (e))
        return {}

    return ret

def del_zone(name):
    client = PowerDNSClient()

    try:
        req = requests.delete(url=client.get_zone_url(name), headers=client.headers, verify=client.verify)
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to delete zone: '%s'" % (e))
        return False

    return ret

def update_zone(name, data):
    client = PowerDNSClient()
    
    try:
        req = requests.put(url=client.get_zone_url(name), data=json.dumps(data), headers=client.headers, verify=client.verify)
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to update zone: '%s'" % (e))
        return False

    return ret

def list_records(zone, detailed=False):
    client = PowerDNSClient()

    try:
        req = requests.get(url=client.get_zone_url(zone), headers=client.headers, verify=client.verify)
        data = client.handle_request(req)['rrsets']
    except Exception as e:
        log.error("Failed to get list of records for zone %s: %s" % (zone, e))
        return {}

    if not detailed:
        ret = []
        for rr in data:
            for record in rr['records']:
                ret.append("{name} {type} {content} {ttl}".format(content = record['content'], **rr) )
        ret = sorted(ret)
    else:
        ret = data
    
    return ret


def get_record(zone, name, type):
    client = PowerDNSClient()

    try:
        req = requests.get(url=client.get_zone_url(zone), headers=client.headers, verify=client.verify)
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to get record %s: %s" % (name, e))
        return False
    
    for rr in ret['rrsets']:
        if rr['name'].lower() == name.lower() and rr['type'].upper() == type:
            return rr

    return {}

def _build_rrsets(changetype, name, type, records, ttl, **kwargs):
    rrset = dict({'name': name, 'type': type, 'changetype': changetype, 'records': records, 'ttl': ttl}, **kwargs)
    return {'rrsets': [rrset]}

def record_exists(zone, name, type, content):
    pass


def set_record(zone, name, type, records=[], **kwargs):
    client = PowerDNSClient()
    default_ttl = 300
    
    rrset = get_record(zone, name, type)
    if 'ttl' not in kwargs:
        if rrset:
            kwargs['ttl'] = rrset['ttl']
        else:
            kwargs['ttl'] = default_ttl
    
    data = _build_rrsets('REPLACE', name, type, records, **kwargs)
    try:
        req = requests.patch(url=client.get_zone_url(zone), data=json.dumps(data), headers=client.headers, verify=client.verify)
        ret = client.handle_request(req)
    except Exception as e:
        log.error("Failed to set record %s: %s" % (name, e))
        return False

    return ret


def del_record(zone, name, type):
    client = PowerDNSClient()

    ret = True
    
    rrset = get_record(zone, name, type)
    if rrset:
        rrset['changetype'] = 'DELETE'
        data = {'rrsets': [rrset]}
        try:
            req = requests.patch(url=client.get_zone_url(zone), data=json.dumps(data), headers=client.headers, verify=client.verify)
            ret = client.handle_request(req)
        except Exception as e:
            log.error("Failed to delete record %s: %s" % (name, e))
            return False

    return ret
