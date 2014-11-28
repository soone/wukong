#!/usr/bin/env python
# *-* coding:utf-8 *-*

import threading, git, time, signal, os, sys
from scapy.all import srp, Ether, ARP, conf

IPSCAN = '192.168.88.1/24'
REPO = "/home/pi/wukong/"
LOCALDB = REPO + "xw_origin.db"
BRANCHNAME = "xiaowu"

HOSTS = {"soone" : ["14:f6:5a:b9:31:4d"], "adou" : ["8c:77:16:b3:8a:ce"], "soone_lenovo" : ["00:12:fe:c8:62:e0"]}
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
        print >> sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        return False

def getDeviceMac():
	res = []
	try:
		ans, unans = srp(Ether(dst="FF:FF:FF:FF:FF:FF")/ARP(pdst=IPSCAN), timeout=2, verbose=False)
	except Exception, e:
                print >> sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
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
            repoAction()
            time.sleep(self.interval)

    def stop(self):
        self.thread_stop = True

def main():
    global hostLastStatus, dbObj
    hostNames = HOSTS.keys()
    hostLastStatus = dict({h: [False, 0, 0] for h in hostNames})
    dbObj = file(LOCALDB, "a+")

    threadObjs = []
    for n in hostNames:
        nThread = MyThread(10, n)
        nThread.start()
        threadObjs.append(nThread)

    pgThread = PushGit(5000)
    pgThread.start()
    threadObjs.append(pgThread)

    # 用来判断网络是否断开，断开重连
    def checkNetwork():
        while True:
            if '192' not in os.popen('ifconfig | grep 192').read():
                print >> sys.stderr, "wifi is down, restart..."
                os.system("/etc/init.d/networking restart")
            time.sleep(300)

    networkThread = threading.Thread(target=checkNetwork)
    networkThread.start()
    threadObjs.append(networkThread)

    def threadExit(signum, frame):
        for t in threadObjs:
            t.stop()

    signal.signal(signal.SIGINT, threadExit)
    signal.signal(signal.SIGTERM, threadExit)

if __name__ == "__main__":
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)
    try:
        pid = os.fork()
        if pid > 0:
            print "Daemon PID %d" % pid
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    hostLastStatus = dict()
    dbObj = 0
    main()
