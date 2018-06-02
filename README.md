# saltstack-powerdns-module
Execution and state modules for PowerDNS Authoritative Server 
------------------------------
### Usage:
```
# The below pillars must present:
powerdns.url: "http://172.16.1.70:8081"
powerdns.api_key: "STRONGPASSWORD"
powerdns.server: localhost # Server Id
powerdns.verify: False # SSL certificate verify
```

#### PowerDNS API Documentation:
https://doc.powerdns.com/authoritative/http-api/zone.html
