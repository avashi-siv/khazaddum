# khazaddum 
Named after [the bridge](//media.giphy.com/media/A6PcmRqkyMOBy/giphy.gif) that dropped Gandalf and the Balrog.

The PacketDropper class is capable of dropping these packets:

- DHCP 
- ARP

Rules created with this script (and tc filter directly) do not persist through reboots.  

Removing a qdisc clears all rules associated with that qdisc.  All rules created with
this module are applied to the root qdisc.  

##### Outdated shell scripts 

buildBridge.sh creates a bridge on a linux device.  It relies on environment variables `$iface0` and `$iface1`.

dropDHCP.sh uses `tc` to match on the [DHCP Message Type](https://tools.ietf.org/html/rfc2132#section-9.6) bit, and drop the packet if it's ACK.  Shoud be generalized.  
