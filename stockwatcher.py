#!/usr/bin/python
# -*- coding: utf-8 -*-
########################################################################
# Name:
# 		stockwatcher.py
# Description:
# 		GUI tools, display stocks in a floating windows.
# Author:
# 		wesley wu
# Python:
#       3.5+
# Version:
#		1.0
########################################################################
from tkinter import *
from tkinter.font import Font
from PIL import Image, ImageTk
from urllib.request import urlopen
import json, time, threading, datetime, base64, io

# ==================define the global variables ========================
# the url of remote stock service
mRemoteStockUrl = 'http://hq.sinajs.cn/list='
mRemoteStockImgUrl = 'http://image.sinajs.cn/newchart/min/n/{}.gif'
# the configuration file for the tools
mConfFile = 'stockwatcher.conf'
# the key name of in the configuration file
mConfSection = 'stocks'
# the click event flag
mOnMouseEnter = False
# the width of the windows
mWinWidth = 400
mMainWinHeight = 25
mMainWinBottomLeftShift = 10
mMainWinBottomUpShift = 40
mPopWinWidth = 545
mPopWinLeftShift = 72
mPopWinUpShift = 340
mPopWinHeight = 300

# define the tat
mUpTag = 'UP'
mEvenTag = 'EVEN'
mDownTag = 'DOWN'
# define the char
mCharUp = '\u25B2'
mCharDown = '\u25BC'
mCharEven = '\u268C'
mCharWin = '\u2600'
mCharLose = '\u2614'
mCharDraw = '\u268C'
mCharWinAlert = '\u2615'
mCharLoseAlert = '\u2702'
# ms time for the speed of text scroll
mCharRefreshSpeed = 200
# the multiplier with the size of the msg
mRefreshMultiplier = 1
# the stock info refresh interval by seconds
mUpdateInterval = 10
mWinIcon = "sw-small.ico"
mWinTitle = "Stock Watcher"
mDetailedWinTitle = "Detailed Info"
mIsMarketCLosed = False


# the main class for the function
class StocksInfoFetcher(object):
    """
    Class of GetStocksInfo
    """
    _instance = None

    # overwrite the new method to creat a singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StocksInfoFetcher, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    # initialize the class
    def __init__(self):
        self.mConfig = self.getConfiguration()

    # read the configuration file
    def getConfiguration(self):
        with open(mConfFile) as configFile:
            config = json.load(configFile)
        return config[mConfSection]

    # get http response
    def getHttpResponse(self, url):
        response = urlopen(url)
        httpContent = response.read().decode('gb2312')
        return str(httpContent)

    # fetch the stocks info
    def getStocksInfo(self):
        # the configuration is none
        if not self.mConfig:
            return

        stocks = []
        for index in range(len(self.mConfig)):
            stocks.append(str(self.mConfig[index]['code']))

        stockCodeNames = ','.join(stocks)
        # print("Stocks: {}".format(stockCodeNames))
        url = mRemoteStockUrl + stockCodeNames
        # print("url: {}".format(url))
        httpContent = self.getHttpResponse(url)
        # print("httpContent: {}".format(httpContent))
        stocksInfoResp = httpContent.split(';')
        # print(stocksInfoResp[1])

        stocksInfoList = []
        costIndex = 0
        for stock in stocksInfoResp:
            line = stock[4:-1]
            kvlist = line.split('=')
            if len(kvlist) < 2:
                continue
            # print(kvlist)
            code = kvlist[0].split('_')[-1]
            dataline = kvlist[1]
            datalist = dataline.split(',')
            # check whether the market is closed or not
            if datalist[31] is not None:
                time = datetime.datetime.strptime(datalist[31], '%H:%M:%S').time()
                self.checkIsMarketClosed(time)

            name = datalist[0][1:100]
            lastclose = datalist[2]
            current = datalist[3]
            if (current > lastclose):
                direction = mCharUp
                styleTag = mUpTag
            elif (current == lastclose):
                direction = mCharEven
                styleTag = mEvenTag
            else:
                direction = mCharDown
                styleTag = mDownTag
            percent = "{:.2f}".format((float(current) - float(lastclose)) / float(lastclose) * 100)
            profit = 0
            profitSign = mCharDraw
            cost, takeprofit, stoploss = self.getOneStocMetrics(code)
            if (cost != 0):
                profit = "{:.2f}".format((float(current) - float(cost)) / float(cost) * 100)
                if (float(profit) > takeprofit):
                    profitSign = mCharWinAlert
                elif (float(profit) > 0.00):
                    profitSign = mCharWin
                elif (float(profit) == 0.00):
                    profitSign = mCharDraw
                elif (float(profit) < stoploss):
                    profitSign = mCharLoseAlert
                else:
                    profitSign = mCharLose
            oneStockContent = " |  {} {} {}({}%) {}({}%) ".format(name, current, direction, percent, profitSign, profit)
            stocksInfoList.append({'code': code, 'tag': styleTag, 'content': oneStockContent})
            costIndex += 1

        return stocksInfoList

    def getOneStocMetrics(self, code):
        for stock in self.mConfig:
            if stock.get('code') == code:
                return stock.get('cost'), stock.get('takeprofit') * 100 ,stock.get('stoploss') * 100

    def checkIsMarketClosed(self, time):
        if time < datetime.datetime.strptime('09:29:59', '%H:%M:%S').time() \
                or (time > datetime.datetime.strptime('11:31:00', '%H:%M:%S').time() \
                            and time < datetime.datetime.strptime('12:59:59', '%H:%M:%S').time()) \
                or time > datetime.datetime.strptime('15:01:00', '%H:%M:%S').time():
            mIsMarketCLosed = True
        else:
            mIsMarketCLosed = False


class StocksController():
    """
    Class StocksController, control the stock display
        the scroll ticker
    """
    # define the static variable
    stockindex = 0
    mStocks = []
    mCodes = []
    mContentLength = 0
    mCurrentTicker = ''

    def __init__(self):
        self.loadMarket()
        # the char index of one stock
        self.index = 0
        self.getStockCodes()
        self.getContentLength()

    def loadMarket(self):
        # get the list of stocks [(code, tag, stock string),]
        stocksInfoFetecher = StocksInfoFetcher()
        StocksController.mStocks = stocksInfoFetecher.getStocksInfo()

    def getStockCodes(self):
        # fill the code, use as tag later
        for stock in StocksController.mStocks:
            code = stock.get('code')
            if code not in StocksController.mCodes:
                StocksController.mCodes.append(code)

    def getContentLength(self):
        contentLen = 0
        for stock in StocksController.mStocks:
            contentLen += len(stock.get('content'))
        StocksController.mContentLength = contentLen

    def getOneTicker(self):
        self.mOneTicker = StocksController.mStocks[self.stockindex]
        self.index = 0
        if StocksController.stockindex + 1 == len(StocksController.mStocks):
            StocksController.stockindex = 0
        else:
            StocksController.stockindex += 1
        return self.mOneTicker.get('content')

    def getNextCharacter(self):
        if self.index == len(StocksController.mCurrentTicker):
            StocksController.mCurrentTicker = self.getOneTicker()
            self.index = 0
        self.mCharacterSymbol = StocksController.mCurrentTicker[self.index:self.index + 1]
        self.index += 1
        return self.mCharacterSymbol

    def getTag(self):
        return self.mOneTicker.get('tag')

    def getCode(self):
        return self.mOneTicker.get('code')


class UpdateThread(threading.Thread):
    """
    Class UpdateThread, subclass of Thread, handle the time to the next update of the stocks values
    """

    def __init__(self):
        self.mStocksController = StocksController()
        threading.Thread.__init__(self)

    def run(self):
        time.sleep(mUpdateInterval)
        self.mStocksController.loadMarket()
        self.run()


class DisplayStockGUI(Frame):
    """
    Class of tkinter.Frame subclass, Initializes the GUI
    """

    def __init__(self, parent):
        # use this flag to refresh the message
        self.mMsgDispCount = 0
        self.mMsgSize = 0
        self.mFinalMsg = ''
        Frame.__init__(self, parent)
        self.parent = parent
        # tags by code name
        # creates an instance of the StocksController class for contents the the data
        self.mStocksController = StocksController()
        self.mCodes = self.mStocksController.mCodes
        self.mPopupWin = False
        self.mCurrentCode = ''
        self.mCurrentImg = ''
        self.mContentOffset = 0
        self.mContentWidth = 0
        self.initGUI()
        self.scrollMsg()
        # start the auto update threading
        self.thread_updating = UpdateThread()
        self.thread_updating.daemon = True
        self.thread_updating.start()

    def initGUI(self):
        # changes the window icon
        self.parent.iconbitmap(mWinIcon)
        self.parent.title(mWinTitle)
        # content LabelFrame to show the ticker scrolling line of text
        self.lblfr_1 = LabelFrame(self.parent)
        self.lblfr_1.pack()
        # Creates a bold font
        self.bold_font = Font(family="Consolas", size=11)
        # the scrolling line of Text for show the data
        self.txt_ticker_widget = Text(self.lblfr_1, background='black', height=2, width=mWinWidth, wrap="none")
        self.txt_ticker_widget.pack(side=TOP, fill=X, expand=True)
        self.txt_ticker_widget.tag_configure(mUpTag, foreground="red", font=self.bold_font)
        self.txt_ticker_widget.tag_configure(mDownTag, foreground="green", font=self.bold_font)
        self.txt_ticker_widget.tag_configure(mEvenTag, foreground="white", font=self.bold_font)
        # self.txt_ticker_widget.tag_configure('sh000001', background="yellow")
        # self.txt_ticker_widget.tag_configure('sz002229', background="blue")
        # self.txt_ticker_widget.tag_configure('sh600030', background="white")
        self.txt_ticker_widget.bind("<Enter>", self.onMouseEnter)
        self.txt_ticker_widget.bind('<Motion>', self.onMouseMove)
        self.txt_ticker_widget.bind("<Leave>", self.onMouseLeave)

    def onMouseMove(self, event):
        code = self.getCodeOnMouseOver(event)
        self.popUpStocksDetailedInfo(code)

    def onMouseEnter(self, event):
        global mOnMouseEnter
        mOnMouseEnter = True


    def onMouseLeave(self, event):
        global mOnMouseEnter
        mOnMouseEnter = False
        self.hidePopupWin()

    def hidePopupWin(self):
        if self.mPopupWin:
            self.mPopupWin.destroy()
            self.mPopupWin = False

    def scrollMsg(self):
        global mOnMouseEnter
        if not mOnMouseEnter:
            self.txt_ticker_widget.configure(state=NORMAL)
            # if we are at the begin of the loop, we should clear the text
            if self.mContentOffset > self.mStocksController.mContentLength:
                self.txt_ticker_widget.delete(1.0)
            self.txt_ticker_widget.insert(END, self.mStocksController.getNextCharacter(),\
                                          (self.mStocksController.getTag(),self.mStocksController.getCode()))
            self.txt_ticker_widget.see(END)
            self.mContentWidth = self.bold_font.measure(self.txt_ticker_widget.get("1.0", "end-1c"))
            # print(self.mContentWidth)
            # print(self.txt_ticker_widget.get("1.0", "end-1c"))
            self.mContentOffset += 1
            self.txt_ticker_widget.configure(state=DISABLED)

        self.txt_ticker_widget.after(mCharRefreshSpeed, self.scrollMsg)

    def getCodeOnMouseOver(self, event):
        # the index position of the total content
        mousePos = event.widget.index("@%s,%s" % (event.x, event.y))
        tmpCodes = self.getCodesFromTags(event)
        for code in tmpCodes:
            code['irange'] = list(event.widget.tag_ranges(code['code']))
            # iterate them pairwise (start and end index)
            for start, end in zip(code['irange'][0::2], code['irange'][1::2]):
                # check if the tag matches the mouse click index
                if event.widget.compare(start, '<=', mousePos) and event.widget.compare(mousePos, '<', end):
                    return code.get('code')


    def getCodesFromTags(self, event):
        tmpCodes = []
        for tag in (event.widget.tag_names() and self.mCodes):
            code = tag
            tmpCodes.append({'code': code, 'irange': []})
        return tmpCodes

    def getRomotePicture(self, url):
        fd = urlopen(url)
        imageFile = io.BytesIO(fd.read())
        fd.close()
        return imageFile

    def popUpStocksDetailedInfo(self, code):
        if not code:
            return

        x = self.parent.winfo_rootx() - mPopWinLeftShift
        y = self.parent.winfo_rooty() - mPopWinUpShift
        ystr = "+{}".format(y)
        if y < 0:
            ystr = "+{}".format(self.parent.winfo_rooty() + 35)

        if self.mPopupWin and code != self.mCurrentCode:
            self.hidePopupWin();

        if not self.mPopupWin:
            x = self.parent.winfo_rootx() - mPopWinLeftShift
            y = self.parent.winfo_rooty() - mPopWinUpShift
            ystr = "+{}".format(y)
            if y < 0:
                ystr = "+{}".format(self.parent.winfo_rooty() + 35)
            # creates a toplevel window
            self.mPopupWin = Toplevel(self.parent)
            # # Leaves only the label and removes the app window
            self.mPopupWin.wm_overrideredirect(True)
            self.mPopupWin.wm_geometry("{}x{}+{}{}".format(mPopWinWidth,mPopWinHeight, x, ystr))
            # url = 'http://image.sinajs.cn/newchart/min/n/sh000001.gif'
            # if (code != self.mCurrentCode or not self.mCurrentImg):
            url = mRemoteStockImgUrl.format(code)
            self.mCurrentImg = self.getRomotePicture(url)
            self.mCurrentCode = code
            origImgData = Image.open(self.mCurrentImg)
            finalImage = ImageTk.PhotoImage(origImgData)  # Keep a reference, prevent GC
            Label(self.mPopupWin, image=finalImage).pack()
            self.mPopupWin.mainloop()

# the main loop
def main():
    root = Tk()
    root.geometry('{}x{}-{}-{}'.format(mWinWidth, mMainWinHeight, mMainWinBottomLeftShift, mMainWinBottomUpShift))
    root.attributes('-alpha', 0.8)
    # border less
    #root.overrideredirect(1)
    # top of all others windows
    root.wm_attributes("-topmost", True)
    # root.attributes("-toolwindow", 1)
    root.resizable(0, 0)
    # root.lift()
    # make the window to stay above all other windows
    DisplayStockGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()