#!/usr/bin/env python
# *-* coding:utf-8 *-*

from scapy.all import srp, Ether, ARP, conf
IPSCAN = '192.168.88.1/24'

def getDeviceMac():
	res = []
	try:
		ans, unans = srp(Ether(dst="FF:FF:FF:FF:FF:FF")/ARP(pdst=IPSCAN), timeout=5, verbose=False)
	except Exception, e:
		print str(e)
		return False
	else:
		for snd, rcv in ans:
			res.append(rcv.sprintf("%Ether.src%"))

	return res

def main():
	print getDeviceMac()

if __name__ == "__main__":
	main()
