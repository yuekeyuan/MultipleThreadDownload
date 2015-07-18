import urllib.request as urllib2
import threading
import sys, math, os, time

class DownLoader():
    """
    这一个类实现给定的url资源的下载。嗯嗯，资源的多线程下载
    """
    def __init__(self, url, destFile=None, threadNumber=8):
        self.url = url
        self.destFile = destFile and self.createDestFile() or destFile
        self.threadNumber = (threadNumber >0 and threadNumber < 16) and threadNumber or 8 #[1,15]
        self.threadControl = []
        self.threads = []
        self.fileLength = 0
        self.initThreadControl()
        self.dir = os.mkdir("tem")
        os.chdir("tem")
        self.threadDownload()
        #self.start()

    def createDestFile(self):
        b = self.url.rsplit("/")
        print(b)
        return b[-1] and b[-1] or "file.downloading"

    def initThreadControl(self):
        """
        产生 self.threadControl
        :return:
        """
        #TODO: below show be done
        #不能够进行多线程下载，threadNumber置1
        #不能够连接等异常，返回相应的代号
        #根据获得的文件，获取文件的信息等内容
        if not self.testThreadDownload():
            self.threadNumber = 1
            control = self.generateThreadInfo(begin=0, end=self.fileLength-1)
            return

        #对文件进行分割，便于分段下载
        #TODO: 完善一下
        piece = math.floor(self.fileLength / self.threadNumber) - 1
        prePiece = 0
        for i in range(self.threadNumber):
            end = prePiece + piece
            control = self.generateThreadInfo(i, begin=prePiece, end=end)
            prePiece = end + 1
            self.threadControl.append(control)
        self.threadControl[self.threadNumber -1]["end"] = self.fileLength-1
        self.threadControl[self.threadNumber -1]["value"] = self.fileLength-1
        print("control: ", self.threadControl)

    def testThreadDownload(self):
        """
        测试是否可以进行多线程下载, 获取文件长度
        """
        fd = None
        isThreadDownload = False
        try:
            header = {"Range":"bytes=0-"}
            url = urllib2.Request(self.url,headers=header)
            fd = urllib2.urlopen(url)
        except urllib2.URLError as e:
            print(e)
            sys.exit(-1)
        info = fd.info().items()
        for key, value in info:
            print(key, " : ", value)
            if key == "Content-Length":
                self.fileLength = int(value)
            elif key == "Content-Range":
                isThreadDownload = True
        return isThreadDownload

    def threadDownloadMethod(self, id, name):
        info = self.threadControl[id]
        fd = None
        try:
            header = {"Range":"bytes={0}-{1}".format(str(info["begin"]), str(info["end"]))}    #"Range":"bytes=%1-%2"  '{0},{1}'.format('kzc',18)
            url = urllib2.Request(self.url,headers=header)
            fd = urllib2.urlopen(url)
        except urllib2.URLError as e:
            print(e)
            sys.exit(-1)
        #开始写文件
        file = open(name, "wb")
        file.write(fd.read())
        print("Ok")

    def threadDownload(self):
        self.threads.clear()
        for i in range(self.threadNumber):
            args = [i, "thread_"+str(i)]
            self.threads.append(threading.Thread(target=self.threadDownloadMethod, args=args))
        for i in range(self.threadNumber):
            self.threads[i].start()
        #timer 函数，测试是否完成下载
        threading.Timer(5, function=self.testFinishDownloading).start()

    #提供thread 下载信息的类
    def generateThreadInfo(self, id, begin=0, end=0, value=None, disable=False):
        if not value:
            value = end
        return {"id":id, "begin": begin, "end": end, "value": value,
            "disable":disable, "threadstatus":"prepared", "current":0}

    def testFinishDownloading(self):
        print("test finish downloading")
        for i in range(self.threadNumber):
            if self.threads[i].is_alive():
                threading.Timer(5, function=self.testFinishDownloading).start()
                return
        #防止伪信息
        time.sleep(1)
        for i in range(self.threadNumber):
            if self.threads[i].is_alive():
                threading.Timer(5, function=self.testFinishDownloading).start()
                return
        self.mergeFile()

    def mergeFile(self):
        file = open(self.destFile, "wb")
        for i in range(self.threadNumber):
            temFile = open("thread_"+str(i), "rb")
            file.write(temFile.read())
            temFile.close()
        file.close()
