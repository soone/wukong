#!/usr/bin/env python
# *-* coding:utf-8 *-*

import threading, git, time
from scapy.all import srp, Ether, ARP, conf

#IPSCAN = '192.168.88.1/24'
IPSCAN = '192.168.0.1/24'
REPO = "/home/soone/code/python/wukong/"
LOCALDB = REPO + "xw_origin.db"
BRANCHNAME = "xiaowu"

HOSTS = {"soone" : ["3c:07:54:31:10:38"]}
REPEATCOUNT = 5

def repoAction():
    repo = git.Repo(REPO)
    try:
        index = repo.index
        index.add([LOCALDB])
        index.commit("home data")

        origin = repo.remotes.origin
        origin.push(BRANCHNAME)

    except Exception, e:
        print str(e)
        return False

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

def checkMacStatus(hostName):
    macs = getDeviceMac()
    for eMac in HOSTS[hostName]:
        if eMac in macs:
            return True

    return False

def inOutHome(hostName):
    global hostLastStatus, dbObj

    macStatus = checkMacStatus(hostName)
    if macStatus == True and hostLastStatus[hostName][0] == False:
        hostLastStatus.update({hostName: [True, int(time.time()), 0]})
        # 记录到达日志
        dbObj.write("%s\tTrue\t%s\n" % (hostName, int(time.time())))
    elif macStatus == False and hostLastStatus[hostName][0] == True:
        # 重试几次确认是离开了
        if hostLastStatus[hostName][2] >= REPEATCOUNT:
            hostLastStatus.update({hostName: [False, int(time.time()), 0]})
            dbObj.write("%s\tFalse\t%s\n" % (hostName, int(time.time())))
        else:
            hostLastStatus[hostName][2] += 1

    dbObj.flush()

class MyThread(threading.Thread):
    def __init__(self, interval, hostName):
        threading.Thread.__init__(self)
        self.interval = interval
        self.hostName = hostName
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            inOutHome(self.hostName)
            time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True

class PushGit(threading.Thread):
    def __init__(self, interval):
        threading.Thread.__init__(self)
        self.interval = interval
        self.thread_stop = False

    def run(self):
        while not self.thread_stop:
            print repoAction()
            time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True

def main():
    global hostNames
    try:
        for n in hostNames:
            nThread = MyThread(10, n)
            nThread.start()

        pgThread = PushGit(100)
        pgThread.start()
    finally:
        nThread.stop()
        pgThread.stop()

if __name__ == "__main__":
    try:
        hostNames = HOSTS.keys()
        hostLastStatus = dict({h: [False, 0, 0] for h in hostNames})
        dbObj = file(LOCALDB, "a+")
        main()
        while(True):
            pass
    finally:
        dbObj.close()

