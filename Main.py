#coding=utf-8
from PyQt4 import QtGui, QtCore, QtWebKit
from DownLoader import DownLoader
import sys

if __name__ == "__main__":
    DownLoader("http://docs.scipy.org/doc/numpy/numpy-html-1.9.1.zip", "hello.zip")