domain.com:
  powerdns_zone.present:
    - kind: master # Default: Native
    - nameservers:
      - ns1.domain.com. # Must end with '.'
      - ns2.domain.com.

domain.com:
  powerdns_zone.present:
    - kind: slave
    - masters:
      - 1.1.1.1
      - 2.2.2.2

web.domain.com:
  powerdns_record.present:
    - zone: domain.com
    - type: A
    - ttl: 3600
    - records:
      - content: 10.10.10.11
        disabled: False # Optional
      - content: 10.10.10.12
    - require:
      - powerdns_zone: domain.com

mail.domain.com:
  powerdns_record.present:
    - zone: domain.com
    - type: A
    - ttl: 700
    - records:
      - content: 10.10.10.101
      - content: 10.10.10.102
    - require:
      - powerdns_zone: domain.com

test.domain.com:
  powerdns_record.present:
    - zone: domain.com
    - type: A
    - ttl: 700
    - records:
      - content: 10.10.10.121
    - require:
      - powerdns_zone: domain.com

domain.com_mx:
  powerdns_record.present:
    - name: domain.com
    - zone: domain.com
    - type: MX
    - ttl: 700
    - records:
      - content: 10 mail.domain.com
      - content: 20 mail.google.com
    - require:
      - powerdns_record: mail.domain.com

app.domain.com:
  powerdns_record.present:
    - zone: domain.com
    - type: CNAME
    - ttl: 7200
    - records:
      - content: web.domain.com.
    - require:
      - powerdns_record: web.domain.com
  

test1.domain.com_delete:
  powerdns_record.absent:
    - name: test1.domain.com
    - zone: domain.com
    - type: A
    - require:
      - powerdns_record: test.domain.com

domain.com_zone_delete:
  powerdns_zone.absent:
    - name: domain.com