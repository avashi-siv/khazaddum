### basic instructions

buildBridge.sh creates a bridge on a linux device.  It relies on environment variables $iface0 and $iface1.

dropDHCP.sh uses `tc to match on the [DHCP Message Type](https://tools.ietf.org/html/rfc2132#section-9.6) bit, and drop the packet if it's ACK.  Shoud be generalized.  
