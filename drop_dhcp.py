import logging
from plumbum import SshMachine, ProcessExecutionError


class CommandFailure(Exception):
    pass

class InvalidArgumentException(Exception):
    pass

class PacketDropper():
    """An object that drops objects using arbitrary bits from tc"""

    def __init__(self, address: str, keyfile: str, user: str = 'starry'):
        self.address = address
        self._machine = SshMachine(address, keyfile, user)
        self._log = logging.getLogger(__name__)

    def remove_qdisc(self, iface: str):
        try:
            self.machine['sudo']('tc', 'qdisc', 'del', 'dev', iface, 'root')
        except ProcessExecutionError as err:
            raise CommandFailure(str(err))

    def drop_DHCP(self, dhcp_type: str, mac_addr: str = None, iface: str):
        """
        Drop DHCP packets moving across this device.  Only blocks packets on
        their way out of the device, i.e. via the egress qdisc.

        :param dhcp_type: Type of DHCP message to block.  See https://tools.ietf.org/html/rfc2132#section-9.6
        :param mac_addr: The DHCP client for which to block DHCP.  No colons.
        :param iface: DHCP is exiting the device via this interface.
        """
        dhcp_types = {
                'discover' : '0x01',
                'offer' : '0x02',
                'request' : '0x03',
                'decline' : '0x04',
                'ack' : '0x05',
                'nak' : '0x06',
                'release' : '0x07',
                'inform' : '0x08'
                }

        if dhcp_type not in dhcp_types:
            raise InvalidArgumentException(f'{dhcp_type} not acceptable.')
        else:
            dhcp_bit = DHCP_types.get(dhcp_type)
        if mac_addr:
            mac_binary = f'{0x{mac_addr}:0>48b}'
            # tc u32 can only match on 32 bits at a time 
            first_mac_binary, second_mac_binary  = mac_binary[:32], mac_binary[32:]
            bitmask1, bitmask2 = '0xffffffff', '0xffff'
        else:
            first_mac_binary, second_mac_binary = f'{0x0:0>32b}', f'{0x0:0>16b}'
            bitmask1, bitmask2 = '0x00000000', '0x0000'

        # create an HTB qdisc on given interface
        self.machine['sudo']('qdisc', 'add', 'dev', iface, 'root',
                'handle', '1:', 'htb', 'default', '10')
        # create a superclass to sort traffic 
        self.machine['sudo']('qdisc', 'add', 'dev', iface, 'root',
                'handle', '1:', 'htb', 'default', '10')
        # create two subclasses, one that matches packets on the filter, one for all others
        for subclassid in '10', '11':
            # HTB requires a rate since it's technically for rate limiting
            # I assume here that 2gbit is above any possible traffic, is that reasonable?
            self.machine['sudo']('class', 'add' 'dev', iface, 'parent',
                    '1:1', 'classid', subclassid, 'htb', 'rate', '2gbit')
        # where the magic happens
        self.machine['sudo']('tc', 'filter', 'add', 'dev', iface,
                'protocol', 'ip', 'parent', '1:', 'pref', '1', 'u32',
                'match', 'ip', 'protocol', '17', '0xff',
                'match', 'u32', first_mac_binary, bitmask1, 'at', '56',
                'match', 'u16', second_mac_binary, bitmask2, 'at', '60',
                'match', 'u8', dhcp_bit, '0xff', 'at', '270',
                'flowid', '1:11', 'action', 'drop')
