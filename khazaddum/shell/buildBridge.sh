#!/bin/bash

brctl addbr br0

brctl addif br0 $iface0 $iface1


