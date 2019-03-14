#!/bin/bash

tc qdisc del dev eth2 root
tc qdisc add dev eth2 root handle 1: htb default 10 
# unclear what's happening here
tc class add dev eth2 parent 1: classid 1:1 htb rate 2gbit

tc class add dev eth2 parent 1:1 classid 1:10 htb rate 2gbit
tc class add dev eth2 parent 1:1 classid 1:11 htb rate 2gbit 

tc filter add dev eth2 protocol ip parent 1: pref 1 u32 \
	match ip protocol 17 0xff \
	match u8 0x05 0xff at 270 \
	flowid 1:11 action drop

#tc -s filter show dev br0
#it only shows up on br0, not sure why
