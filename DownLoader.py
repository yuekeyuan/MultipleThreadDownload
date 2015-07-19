import hashlib
import urllib.request as urllib2
import sys, math, os, time, json, threading

"""
1:现在实现数据控制和线程控制分离
2:现在实现线程可控的下载 #TODO:
3:整理代码
4:实现线程终止后 重启线程的下载
"""
class DownLoader():
    def __init__(self, url, destFile=None, threadNumber=8):
        self.url = url
        self.destFile = self.createDestFile(destFile)
        self.dirName = hashlib.md5(self.url.encode(encoding='utf-8')).hexdigest()
        self.threadNumber = (threadNumber >0 and threadNumber < 16) and threadNumber or 8 #[1,15]
        self.threads = []
        self.threadControl = {}
        self.threadControl["process"] = {}
        self.threadControl["thread"] = []
        self.threadControl["data"]  = []
        self.threadControl["process"]["dataNumber"] = 0
        self.threadControl["merge"] = []
        self.fileLength = 0
        self.stopDownloading = False
        if not (self.dirName in os.listdir()):
            os.mkdir(self.dirName)
        os.chdir(self.dirName)

        self.initThreadControl()
        self.threadDownload()
        #停止下载的测试
        threading.Timer(5, self.stopDownload).start()
        threading.Timer(8, self.restartDownloading).start()

    def stopDownload(self):
        self.stopDownloading = True
        for i in range(self.threadNumber):
            if self.threadControl["thread"][i]["status"] != "finished":
                self.threadControl["thread"][i]["status"] = "stopped"

    def restartDownloading(self):
        print("restart downloading")
        self.stopDownloading = False
        for i in range(self.threadNumber):
            if self.threadControl["thread"][i]["status"] == "stopped":
                self.threadControl["thread"][i]["status"] == "unfinished"
                self.restartStoppedThread(i)
        #timer 函数，测试是否完成下载
        threading.Timer(1, function=self.testFinishDownloading).start()

    def restartStoppedThread(self, id=None):
        print("restart stopped thread")
        if id ==None:
            for i in range(self.threadNumber):
                self.restartThread(i)
        else:
            #TODO: 更新 data 和 thread 信息
            self.threadControl["thread"][id]["status"] = "unfinished"
            dataId = self.threadControl["thread"][id]["dataId"]
            start = self.threadControl["data"][dataId]["begin"]
            current = self.threadControl["data"][dataId]["current"]
            end = self.threadControl["data"][dataId]["end"]
            currentCursor = start + current

            print("old data control: ", self.threadControl["data"][dataId])
            #更新第一部分的值
            self.threadControl["data"][dataId]["value"] = currentCursor
            self.threadControl["data"][dataId]["status"] = "finished"

            #更新第二部分的值
            newDataId = self.threadControl["process"]["dataNumber"]
            newData = self.generateDataInfo(id=newDataId, begin=currentCursor, value=end, end=end)
            self.threadControl["process"]["dataNumber"] = newDataId + 1
            self.threadControl["data"].append(newData)
            self.threadControl["merge"].insert(self.threadControl["merge"].index(dataId)+1,newDataId)
            print(self.threadControl["merge"])
            self.threadControl["thread"][id]["dataId"] = newDataId
            args = [id,]
            #启动thread
            thread = threading.Thread(target=self.threadDownloadMethod, args=args)
            self.threads[id] = thread

            print("changed data control: ", self.threadControl["data"][dataId])
            print("new data control:     ", self.threadControl["data"][newDataId])
            f = open("json.json", "w")
            json.dump(self.threadControl, f)
            f.close()
            self.threads[id].start()

    def regenerateThread(self, id):
        """
        这个函数是用于thread 完成工作后，对任务进行再分配的一个函数
        """
        #TODO: getAndGeneratedataInfo(id)
        dataId = self.getAndGenerateDataInfo(id)
        args = [id,]
        self.threads[id] =  threading.Thread(target=self.threadDownloadMethod, args=args)
        self.threads[id].start()

    def getAndGenerateDataInfo(self, id):
        #TODO:编写这一个函数，让它能够产生新的thread info 和 data info 用于下载
        pass

    def createDestFile(self, destFile=None):
        if not destFile:
            return destFile
        b = self.url.rsplit("/")
        return b[-1] and b[-1] or "file.downloading"

    def initThreadControl(self):
        #线程和进程的控制信息的初始化。
        result = self.testThreadDownload()
        self.threadControl["process"]["fileLength"] = self.fileLength

        #只能单进程下载的文件
        if not result:
            self.threadNumber = 1
            dataId = self.initDataControl(1)
            control = self.generateThreadInfo(0, dataId=dataId)
            self.threadControl["thread"].append(control)
            self.threadControl["process"]["threadNumber"] = self.threadNumber
            self.threadControl["process"]["downloadType"] = "singleThread"
            return

        #多进程下载的文件处理
        #对文件进行分割，便于分段下载
        self.initDataControl(self.threadNumber)
        for i in range(self.threadNumber):
            control = self.generateThreadInfo(i, dataId=i)
            self.threadControl["thread"].append(control)
        self.threadControl["process"]["threadNumber"] = self.threadNumber
        self.threadControl["process"]["downloadType"] = "multipleThread"
        print("control: ", self.threadControl)

    def initDataControl(self,blockNumber):
        if blockNumber == 1:
            data = self.generateDataInfo(0, self.fileLength-1, id=0)
            self.threadControl["data"].append(data)
            self.threadControl["merge"].append(self.threadControl["process"]["dataNumber"])
            self.threadControl["process"]["dataNumber"] = 1
            return 0

        #将下载区域初始化等分为 blockNumber 块
        piece = (self.fileLength-self.threadNumber) / blockNumber
        prePiece = 0
        for i in range(self.threadNumber):
            if i == self.threadNumber-1:
                data = self.generateDataInfo(begin=int(prePiece), end=self.fileLength-1,id=i)
            else:
                end = prePiece + piece
                data = self.generateDataInfo(begin=int(prePiece), end=int(end),id=i)
                prePiece = end + 1
            self.threadControl["data"].append(data)
            self.threadControl["merge"].append(self.threadControl["process"]["dataNumber"])
            self.threadControl["process"]["dataNumber"] = self.threadControl["process"]["dataNumber"] + 1
        return "OK"

    def testThreadDownload(self):
        """
        测试是否可以进行多线程下载, 获取文件长度
        """
        print("run here")
        fd = None
        isThreadDownload = False
        try:
            header = {"Range":"bytes=0-"}
            url = urllib2.Request(self.url,headers=header)
            fd = urllib2.urlopen(url)
        except urllib2.URLError as e:
            print(e.reason)
            sys.exit(-1)

        info = fd.info().items()
        for key, value in info:
            print(key, " : ", value)
            if key == "Content-Length":
                self.fileLength = int(value)
            elif key == "Content-Range":
                isThreadDownload = True
        return isThreadDownload

    def threadDownloadMethod(self, id):
        dataId = self.threadControl["thread"][id]["dataId"]
        info = self.threadControl["data"][dataId]
        name = "thread_" + str(self.threadControl["data"][dataId]["id"])
        fd = None
        try:
            header = {"Range":"bytes={0}-{1}".format(str(info["begin"]), str(info["end"]))}    #"Range":"bytes=%1-%2"  '{0},{1}'.format('kzc',18)
            url = urllib2.Request(self.url,headers=header)
            fd = urllib2.urlopen(url)
        except urllib2.URLError as e:
            print(e)
            #TODO: 这里应该实现远程主机关闭连接的之后的运行工作，或是其他的bug，遇到过,所以这里提及一下
            sys.exit(-1)

        #开始写文件
        file = open(name, "wb")
        writeLength = 0                 #已经写入的文件长度
        while True:
            #处理 停止下载的事件
            if self.threadControl["thread"][id]["status"] == "stopped":
                self.threadControl["data"][dataId]["current"] = writeLength
                print("stop execution")
                return

            data = fd.read(4096)
            totalLength = self.threadControl["data"][dataId]["value"] - self.threadControl["data"][dataId]["begin"] + 1

            if not len(data):
                break
            if writeLength + len(data) > totalLength:
                sliceLength = totalLength - writeLength
                data = data[0:sliceLength]
                file.write(data)
                writeLength = writeLength + len(data)
                self.threadControl["data"][dataId]["current"] = writeLength
                break
            else:
                file.write(data)
                writeLength = writeLength + len(data)
                self.threadControl["data"][dataId]["current"] = writeLength
        print("thread:", id, "  write length:", writeLength)
        self.threadControl["thread"][id]["status"] = "finished"
        file.close()

    def threadDownload(self):
        self.threads.clear()
        for i in range(self.threadNumber):
            args = [i,]
            self.threads.append(threading.Thread(target=self.threadDownloadMethod, args=args))
        for i in range(self.threadNumber):
            self.threads[i].start()
        #timer 函数，测试是否完成下载
        threading.Timer(1, function=self.testFinishDownloading).start()
    #提供thread 下载信息的类
    def generateThreadInfo(self, id, status="prepared", dataId=None):
        return {"id":id,"status":"prepared", "dataId":dataId}

    def generateDataInfo(self, begin=0, end=0, value=None, current=0, status="unfinished", id=0):
        if value == None:
            value = end
        return {"begin": begin, "end": end, "value": value, "status":status, "current":0, "id":id}

    def testFinishDownloading(self):
        print("test finish downloading")
        if self.stopDownloading:
            for i in range(self.threadNumber):
                if self.threads[i].is_alive():
                    threading.Timer(0.5, function=self.testFinishDownloading).start()
                    return
            print("the downloading has been stopped and we don't need to test it any more")
            jsonFile = open("hello.json", "w")
            json.dump(self.threadControl, jsonFile,indent=4)
            jsonFile.close()
            return

        count = 0
        for i in range(self.threadNumber):
            dataId = self.threadControl["thread"][i]["dataId"]
            count = self.threadControl["data"][dataId]["current"] + count

        print("percentage: ", count/self.fileLength, "count: ", count/(1024*1024), "M")

        for i in range(self.threadNumber):
            if self.threads[i].is_alive():
                threading.Timer(2, function=self.testFinishDownloading).start()
                return
        #防止伪信息
        time.sleep(1)
        for i in range(self.threadNumber):
            if self.threads[i].is_alive():
                threading.Timer(2, function=self.testFinishDownloading).start()
                return
        self.mergeFile()

    def mergeFile(self):
        print("start to merge file")
        file = open(self.destFile, "wb")
        for i in self.threadControl["merge"]:
            print(i)
            temFile = open("thread_"+str(i), "rb")
            file.write(temFile.read())
            temFile.close()
        file.close()
        print("total file size:", os.path.getsize(self.destFile))
        jsonFile = open("hello.json", "w")
        json.dump(self.threadControl, jsonFile,indent=4)
        jsonFile.close()