#!/usr/bin/env python3
# coding=utf-8

import base64
import datetime
import os
import re
import shutil
import ssl
import sys
import stat
from urllib import request


def getLastestIpData():
    url = "http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest"
    print('[Note] Try to get IP data from ' + url + ' ....')
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36"
    headers = {'User-Agent': user_agent}
    myreq = request.Request(url, None, headers)
    usable = r'^apnic\|CN\|ipv4\|([^|]*)\|(\d+)'
    tmpFile = None
    # comment_pattern = r'^\W*#(.*)$'
    # ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    baseFold = "/tmp"
    rulesFile = "/jffs/etc/chn_set.nft"
    regs = re.compile(usable)
    # nft table name e.g. ip tablename | inet tablename
    tableName = "ip xray"
    # nft set name
    setName = "chn"
    ips = []
    try:
        response = request.urlopen(myreq)
        dataContent = response.read()
        print('[Note] Get IP data success! Data length is ' + str(len(dataContent)) + '.')
        logFile = open(baseFold + '/cnip.log', 'wb')
        nftrule = open(baseFold + '/cnip.nft', 'w')
        nftrule.write("#!/usr/sbin/nft -f\n")
        nftrule.write('\n# updated on ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
        nftrule.write("table " + tableName + " {\n")
        nftrule.write("    set " + setName + " { type ipv4_addr; flags interval\n")
        nftrule.write("        elements = {\n\t\t\t")
        try:
            logFile.write(dataContent)
            logFile.close()
            tmpFile = open(baseFold + '/cnip.log', 'r')
            for line in tmpFile.readlines():
                if regs.search(line):
                    data = regs.findall(line)[0]
                    # mask:
                    # 256 / 24
                    # 512 / 23
                    # 1024 / 22
                    # 2048 / 21
                    # 4096 / 20
                    # 8192 / 19
                    # 16384 / 18
                    # 32768 / 17
                    # 65536 / 16
                    # 131072 / 15
                    # 262144 / 14
                    # 524288 / 13
                    # 1048576 / 12
                    # 2097152 / 11
                    # 4194304 / 10
                    for i in range(10, 24):
                        if int(data[1]) == (2 ** (32 - i)):
                            ip = data[0] + '/' + str(i)
                            ips.append(ip)
            # print(ips)
            for j in range(1, len(ips)):
                if j % 3 == 0:
                    nftrule.write(ips[j-1] + ',\n\t\t\t')
                else:
                    nftrule.write(ips[j-1] + ', ')
            nftrule.write(ips[-1])

            tmpFile.close()
            nftrule.write("\n\t\t}\n\t}\n}\n")
            nftrule.close()
            shutil.move(baseFold + "/cnip.nft", rulesFile)
            os.chmod(rulesFile, stat.S_IRWXU + stat.S_IXGRP + stat.S_IXOTH + stat.S_IROTH)
        except Exception as e:
            print(e)
            print('[Note] Program exit...')
            tmpFile.close()
            nftrule.close()
            sys.exit()

    except Exception as e:
        print(e)
        print('[Note] Program exit...')
        sys.exit()


if __name__ == "__main__":
    getLastestIpData()
    print('[Note] Finish!')
