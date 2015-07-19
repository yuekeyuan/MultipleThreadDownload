#coding=utf-8
from PyQt4 import QtGui, QtCore, QtWebKit
from DownLoader import DownLoader
import sys

if __name__ == "__main__":
    #DownLoader("http://dx.cr173.com/soft1/iSilo.rar", "hello.zip", 8)
    #DownLoader("http://yuekeyuan.duapp.com/", "a.txt", 15)
    DownLoader("http://docs.scipy.org/doc/numpy/numpy-html-1.9.1.zip", "hello.zip", 15)