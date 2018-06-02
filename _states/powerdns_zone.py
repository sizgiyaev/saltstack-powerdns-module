# -*- coding: utf-8 -*-
'''
'''

import logging

__virtualname__ = 'powerdns_zone'

log = logging.getLogger(__name__)

def __virtual__():
    if 'powerdns.get_zone' in __salt__:
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

def _collect_changes(old, new):
    changes = {'old': {}, 'new': {}}
    for key in new:
        if old[key] != new[key]:
            changes['old'][key] = old[key]
            changes['new'][key] = new[key]
    return changes

def present(name, kind='native', nameservers=[], masters=[]):
    
    name = _canonicalize_string(name)

    ret = {'name': name,
        'changes': {},
        'result': False,
        'comment': ''}

    zone_new = {
        'kind': kind.title(),
        'masters': masters
    }
    zone_old = __salt__['powerdns.get_zone'](name)
    if zone_old:
        changes = _collect_changes(zone_old, zone_new)
        ret['result'] = True
        if changes['new']:
            ret['changes'] = { name: changes }
            if __salt__['powerdns.update_zone'](name, zone_new):
                ret['comment'] = "Zone updated."
            else:
                ret['result'] = False
                ret['comment'] = "Zone not updated."
        else:
            ret['comment'] = "Zone already present."
        return ret

    zone_new['nameservers'] = nameservers
    zone = __salt__['powerdns.add_zone'](name, zone_new)
    if zone:
        ret['result'] = True
        ret['comment'] = 'Zone present.'
        ret['changes'] = { name : { 'old': '', 'new': zone } }
        
    return ret

def absent(name):
    
    name = _canonicalize_string(name)

    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}
    if not __salt__['powerdns.zone_exists'](name):
        ret['result'] = True
        ret['comment'] = 'Zone already absent.'
        return ret
    else:
        zone = __salt__['powerdns.get_zone'](name)

    if __salt__['powerdns.del_zone'](name):
        ret['result'] = True
        ret['comment'] = 'Zone absent.'
        ret['changes'] = { name : { 'old': zone, 'new': '' } }
        
    return ret