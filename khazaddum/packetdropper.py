"""Main packet dropping class"""
import logging
from plumbum import SshMachine, ProcessExecutionError

class CommandFailure(Exception):
    """Pass on plumbum issues"""

class InvalidArgumentException(Exception):
    """Users are stupid"""

class PacketDropper():
    """An object that drops objects using arbitrary bits from tc"""

    def __init__(self, address: str, keyfile: str, user: str = 'starry'):
        self.address = address
        self._machine = SshMachine(host=address, keyfile=keyfile, user=user)
        self._log = logging.getLogger(__name__)
        self._log.
        self._pref = 0

    def remove_qdisc(self, iface: str):
        """Clear the root qdisc

        This is the qdisc that this module works on.  The qdisc should be
        cleared every time a new instance of PacketDropper is created,
        or there will be conflicts with rule priorities.
        """
        try:
            self._machine['sudo']('tc', 'qdisc', 'del', 'dev', iface, 'root')
        except ProcessExecutionError as err:
            self._log.warning('Plumbum failed')
            raise CommandFailure(str(err))
        self._log.info("Qdisc deleted")

    def _setup_classes(self, iface: str):
        # create an HTB qdisc on given interface
        self._machine['sudo']('tc', 'qdisc', 'add', 'dev', iface, 'root',
                'handle', '1:', 'htb', 'default', '10')
        # create a superclass to sort traffic
        self._machine['sudo']('tc', 'qdisc', 'add', 'dev', iface, 'root',
                'handle', '1:', 'htb', 'default', '10')
        # create two subclasses, one that matches packets on the filter, one for all others
        for subclassid in '10', '11':
            # HTB requires a rate since it's technically for rate limiting
            # I assume here that 2gbit is above any possible traffic, is that reasonable?
            self._machine['sudo']('tc', 'class', 'add' 'dev', iface, 'parent',
                    '1:1', 'classid', subclassid, 'htb', 'rate', '2gbit')
        self._pref += 1
        self._log.info("Qdisc and classes created")

    def drop_dhcp(self, dhcp_type: str, iface: str, mac_addr: str = None):
        """
        Drop DHCP packets moving across this device.  Only blocks packets on
        their way out of the device, i.e. via the egress qdisc.

        :param dhcp_type: Type of DHCP message to block,
                          see https://tools.ietf.org/html/rfc2132#section-9.6
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
        dhcp_bit = dhcp_types.get(dhcp_type)
        if mac_addr:
            mac_binary = bin(int(mac_binary), 16)[2:]
            # add leading zeroes
            mac_binary = mac_binary.zfill(48)
            # tc u32 can only match on 32 bits at a time
            first_mac_binary, second_mac_binary = mac_binary[:32], mac_binary[32:]
            bitmask1, bitmask2 = '0xffffffff', '0xffff'
        else:
            first_mac_binary, second_mac_binary = f'{0x0:0>32b}', f'{0x0:0>16b}'
            bitmask1, bitmask2 = '0x00000000', '0x0000'

        self._setup_classes(iface)

        # where the magic happens
        try:
            self._machine['sudo']('tc', 'filter', 'add', 'dev', iface,
                    'protocol', 'ip', 'parent', '1:', 'pref', self._pref, 'u32',
                    'match', 'ip', 'protocol', '17', '0xff',
                    'match', 'u32', first_mac_binary, bitmask1, 'at', '56',
                    'match', 'u16', second_mac_binary, bitmask2, 'at', '60',
                    'match', 'u8', dhcp_bit, '0xff', 'at', '270',
                    'flowid', '1:11', 'action', 'drop')
        except ProcessExecutionError as err:
            self._log.warning('Plumbum failed')
            raise CommandFailure(str(err))
        self._log.info("Qdisc deleted")
        log_msg = "Dropping DHCP"
        if mac_addr:
            log_msg += f" to {mac_addr}"
        log_msg += f" on {iface}"
        self._log.info(log_msg)

    def drop_arp(self, iface: str):
        """Drop ARP packets on the given interface

        :param iface: The interface on which to drop outgoing ARP packets
        """
        self._setup_classes(iface)

        # www.funtoo.org/Traffic_Control
        self._machine['sudo']('tc', 'filter', 'add', 'dev', iface,
                'protocol', 'ip', 'parent', '1:', 'pref', self._pref, 'u32',
                'match', 'u16', '0x0806', '0xffff', 'at', '4'
                'flowid', '1:11', 'action', 'drop')
