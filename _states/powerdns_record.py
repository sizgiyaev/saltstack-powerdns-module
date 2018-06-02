# -*- coding: utf-8 -*-
'''
'''

import logging

NOT_CANONICALIZE_TYPES = ['A', 'AAAA']

__virtualname__ = 'powerdns_record'

log = logging.getLogger(__name__)

def __virtual__():
    if 'powerdns.get_record' in __salt__:
        return __virtualname__
    log.error('The powerdns execution module is not present.')
    return False

# TODO: Implement test capability
def test(name, *args, **kwargs):
    zzz = __salt__['powerdns.argtest'](args, **kwargs)
    ret = {'name': name,
           'changes': {},
           'result': zzz,
           'comment': ''}

    return ret

def _canonicalize_string(name):
    if not name.endswith('.'):
        return name + '.'
    else:
        return name

def _complete_records(records=[]):
    for record in records:
        if 'disabled' not in record.keys():
            record['disabled'] = False
        # TODO: Decide necessity
        # if 'set-ptr' not in record.keys():
        #     record['set-ptr'] = False
    return records

def present(zone, name, type, records, ttl):
    
    name = _canonicalize_string(name)

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}
   
    if type.upper() not in NOT_CANONICALIZE_TYPES:
        for record in records:
            record['content'] = _canonicalize_string(record['content'])
    
    records = _complete_records(records)

    record_old = __salt__['powerdns.get_record'](zone, name, type)
    if record_old:
        no_changes = True
        if ttl != record_old['ttl']:
            ret['changes'] = {name : {'old': {'ttl': record_old['ttl']}, 'new': {'ttl': ttl} }}
            no_changes = False
        if records != record_old['records']:
            ret['changes'] = {name : {'old': {'records': record_old['records']}, 'new': {'records': records} }}
            no_changes = False
        if no_changes:
            ret['result'] = True
            ret['comment'] = "Record already present."
            return ret
            
        ret['comment'] = "Record updated."
    else:
        ret['comment'] = "Record present."

    if __salt__['powerdns.set_record'](zone, name, type, records, ttl=ttl):
        ret['result'] = True
        ret['changes'] = { name : { 'new': { 'zone': zone, 'name': name, 'type': type, 'ttl': ttl, 'records': records }, 'old': {} } }
    else:
        ret['result'] = False
        ret['comment'] = "Failed to set Record."
    
    return ret

def absent(zone, name, type):
    
    name = _canonicalize_string(name)
    
    ret = {'name': name,
        'changes': {},
        'result': False,
        'comment': ''}

    record = __salt__['powerdns.get_record'](zone, name, type)
    if record:
        if __salt__['powerdns.del_record'](zone, name, type):
            ret['result'] = True
            ret['comment'] = "Record absent."
            ret['changes'] = { name : { 'new': {}, 'old': record } }
        else:
            ret['result'] = False
            ret['comment'] = "Failed to delete Record."
    else:
        ret['result'] = True
        ret['comment'] = "Record already absent."
    
    return ret
