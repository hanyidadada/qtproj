# This Python file uses the following encoding: utf-8
import os
import re
import sys
import time
import random
import socket
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtWidgets import QHeaderView, QAbstractItemView, QTableView
from PySide6.QtCore import QFile, QThread, Qt, QMutex, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtUiTools import QUiLoader
from handledata import HandleData

qmtx = QMutex()


def validate_mac(mac):
    # 以'-'作为分隔符
    if mac.find('-') != -1:
        pattern = re.compile(r"^\s*([0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}\s*$")
        if pattern.match(mac):
            return True
        else:
            return False

    # 以':'作为分隔符
    if mac.find(':') != -1:
        pattern = re.compile(r"^\s*([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\s*$")
        if pattern.match(mac):
            return True
        else:
            return False


class WorkThread(QThread):
    # 定义一个信号
    trigger = Signal(str)

    def __init__(self, parent=None):
        super(WorkThread, self).__init__(parent)
        # 设置工作状态与初始num数值
        self.working = False
        self.num = 0

    def __del__(self):
        # 线程状态改变与线程终止
        self.working = False
        self.wait()

    def run(self):
        while True:
            if self.working:
                # 等待5秒后，给触发信号，并传递test
                self.trigger.emit('test2')
                self.num += 1
#                print(self.num)
                time.sleep(10)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.macconfigflag = False
        self.info = ""
        self.msg_box = []
        for v in range(10):
            self.msg_box.append(QMessageBox())
        self.load_ui()
        self.ui.smacline.setMaxLength(17)
        self.ui.rmacline.setMaxLength(17)
        self.ui.ctrl1line.setMaxLength(8)
        self.ui.ctrl2line.setMaxLength(8)
        self.ui.configbn.clicked.connect(self.configmac)
        self.ui.sendbn.clicked.connect(self.sendinfo)
        self.sysregtableInit()
        self.init0tabletableInit()
        self.init1tabletableInit()
        self.init3tabletableInit()
        self.init4tabletableInit()
        self.taraget0tabletableInit()
        self.taraget1tabletableInit()
        self.taraget3tabletableInit()
        self.taraget4tabletableInit()
        self.handleData = HandleData()
        self.worker = WorkThread()
        self.worker.trigger.connect(self.updateData)
        self.worker.start()

    def load_ui(self):
        self.desktop = QApplication.instance().screens()[0].size()
        self.screenheight = self.desktop.height()
        self.screenwidth = self.desktop.width()
        self.height = int(self.screenheight * 0.9)
        self.width = int(self.screenwidth * 0.9)
        self.resize(self.width, self.height)
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        self.setCentralWidget(self.ui)
        self.setWindowTitle("sg测试工具")

    def sendinfo(self):
        flag = 0
        if len(self.handleData.send_mac) != 17 or not validate_mac(self.handleData.send_mac):
            flag = 1
        if len(self.handleData.receive_mac) != 17 or not validate_mac(self.handleData.receive_mac):
            flag = 2
        if flag > 0:
            self.messageDialog(1, "警告", "收发mac未配置，请配置后重试")
            return
        self.ctrl1 = self.ui.ctrl1line.text()
        self.ctrl2 = self.ui.ctrl2line.text()
        length = self.ui.lengthline.text()
        globaladdr = self.ui.globaladdrline.text()
        channel = self.ui.directionBox.currentText()
        configreq = self.ui.configreqBox.currentText()
        configwr = self.ui.configwrBox.currentText()
        configclr = self.ui.configclrBox.currentText()
        sendata = self.ui.configdatatext.toPlainText()
        if self.ctrl1 != "" and len(self.ctrl1) == 8:
            qmtx.lock()
            self.handleData.recievelock.acquire()
            self.handleData.receive_data_content = []
            self.handleData.recievelock.release()
            self.handleData.receive_data(1)
            self.handleData.config_data( "5", "全局配置", "配置请求有效", "写", "否", "000000b0", self.ctrl1)
            self.handleData.send_data()
            self.handleData.receive_data_process.join()
            self.messageDialog(2, "成功", "写ctrl1成功!")
            flag += 1
            qmtx.unlock()
        if self.ctrl2 != "" and len(self.ctrl2) == 8:
            qmtx.lock()
            self.handleData.recievelock.acquire()
            self.handleData.receive_data_content = []
            self.handleData.recievelock.release()
            self.handleData.receive_data(1)
            self.handleData.config_data( "5", "全局配置", "配置请求有效", "写", "否", "000000c0", self.ctrl2)
            self.handleData.send_data()
            self.handleData.receive_data_process.join()
            self.messageDialog(3, "成功", "写ctrl2成功!")
            flag += 1
            qmtx.unlock()
        if sendata != "" and globaladdr != "" and length != "":
            qmtx.lock()
            self.handleData.recievelock.acquire()
            self.handleData.receive_data_content = []
            self.handleData.recievelock.release()
            self.handleData.receive_data(1)
            self.handleData.config_data(length, channel, configreq, configwr, configclr, globaladdr, sendata)
            self.handleData.send_data()
            self.handleData.receive_data_process.join()
            self.messageDialog(4, "成功", "自定义数据读写成功！返回值：" + self.handleData.receive_data_content[0])
            flag += 1
            qmtx.unlock()
        if flag == 0:
            self.messageDialog(1, "警告", "发送参数错误！请检查！")
        return

    def messageDialog(self, num, title, str):
        # 核心功能代码就两行，可以加到需要的地方
        if title == "成功":
            self.msg_box[num].setIcon(QMessageBox.Information)
        else:
            self.msg_box[num].setIcon(QMessageBox.Critical)
        self.msg_box[num].setText(str)
        self.msg_box[num].setWindowTitle(title)
        self.msg_box[num].show()

    def configmac(self):
        flag = 0
        self.handleData.send_mac = self.ui.smacline.text()
        if len(self.handleData.send_mac) != 17 or not validate_mac(self.handleData.send_mac):
            flag = 1
        self.handleData.receive_mac = self.ui.rmacline.text()
        if len(self.handleData.receive_mac) != 17 or not validate_mac(self.handleData.receive_mac):
            flag = 2
        if flag == 1:
            self.messageDialog(0, '警告', 'mac发送地址配置出错！请重试！')
            return
        elif flag == 2:
            self.messageDialog(0, '警告', 'mac接收地址配置出错！请重试！')
            return
        self.messageDialog(0, '成功', 'mac地址配置完成！')
        self.handleData.config_port()
        self.macconfigflag = True
        self.worker.working = True

    def updateData(self, data):
        qmtx.lock()
        self.handleData.recievelock.acquire()
        self.handleData.receive_data_content = []
        self.handleData.recievelock.release()
        self.handleData.receive_data(98)
#        self.handleData.config_data( "6", "全局配置", "配置请求有效", "读", "否", "00000000", "00000000000000")
#        self.handleData.send_data()
        self.querysysreg()
        self.queryinitreg(10)
        self.queryinitreg(20)
        self.queryinitreg(30)
        self.queryinitreg(40)
        self.queryinitreg(11)
        self.queryinitreg(21)
        self.queryinitreg(31)
        self.queryinitreg(41)
        self.handleData.receive_data_process.join()
        self.handleData.recievelock.acquire()
        if len(self.handleData.receive_data_content) < 98:
            if len(self.handleData.receive_data_content) == 0:
                self.messageDialog(3, "警告", '接收数据丢失！请检查, 将在下一次更新！')
            else:
                self.messageDialog(3, "警告", '接收数据丢失！请检查, 将在下一次更新！num:' +
                    str(len(self.handleData.receive_data_content)) +
                    ', 第一组数据为：' + self.handleData.receive_data_content[0] +
                    ', 最后第二组数据为：' + self.handleData.receive_data_content[-2] +
                    ', 最后一组数据: ' + self.handleData.receive_data_content[-1])
            self.macconfigflag = False
            self.worker.working = False
            self.handleData.recievelock.release()
            qmtx.unlock()
            return
        if len(self.handleData.receive_data_content[0]) > 8:
            del self.handleData.receive_data_content[0]
        for v in range(0, 10):
            index = self.sysregmodel.index(v, 1)
            self.sysregmodel.setData(index,  self.handleData.receive_data_content[v], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.init0model.index(v, 1)
            self.init0model.setData(index, self.handleData.receive_data_content[(v + 10)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.init1model.index(v, 1)
            self.init1model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*1)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.init3model.index(v, 1)
            self.init3model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*2)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.init4model.index(v, 1)
            self.init4model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*3)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.taraget0model.index(v, 1)
            self.taraget0model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*4)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.taraget1model.index(v, 1)
            self.taraget1model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*5)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.taraget3model.index(v, 1)
            self.taraget3model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*6)], Qt.DisplayRole)
        for v in range(0, 11):
            index = self.taraget4model.index(v, 1)
            self.taraget4model.setData(index, self.handleData.receive_data_content[(v + 10 + 11*7)], Qt.DisplayRole)
        self.handleData.recievelock.release()
        qmtx.unlock()

    def querysysreg(self):
        for v in range(1, 11):
            offset = '{:02X}'.format(v*16)
            self.handleData.config_data( "5", "全局配置", "配置请求有效", "读", "否", "000000" + offset, "0000000" + str(random.randint(0,9)))
            self.handleData.send_data()

    def queryinitreg(self, num):
        for v in [1, 2, 3, 7, 8, 9, 10, 11]:
            offset = '{:03X}'.format(v*16)
            self.handleData.config_data( "6", "全局配置", "配置请求有效", "读", "否", "000"+ str(num)+ offset, "0000000000000000" )
            self.handleData.send_data()
        self.handleData.config_data( "5", "全局配置", "配置请求有效", "读", "否", "000"+ str(num)+ "f20", "00000000" )
        self.handleData.send_data()
        self.handleData.config_data( "6", "全局配置", "配置请求有效", "读", "否", "000"+ str(num)+ "f30", "00000000" )
        self.handleData.send_data()
        self.handleData.config_data( "6", "全局配置", "配置请求有效", "读", "否", "000"+ str(num)+ "f40", "0000000000000000" )
        self.handleData.send_data()

    def sysregtableInit(self):
        self.sysregmodel = QStandardItemModel(0, 2)
        self.sysregmodel.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.sysregtable.setModel(self.sysregmodel)
        # 所有列自动拉伸，充满界面
        self.ui.sysregtable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.sysregtable.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.sysregtable.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.sysregtable.setEditTriggers(QTableView.NoEditTriggers)
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fpga_timestamp'),])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fpga_version'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fpga_dna_high'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fpga_dna_middle'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fpga_dna_low'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fpga_temper'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'xaui_status'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'fc_link'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'function_switch0'), ])
        self.sysregmodel.appendRow([QStandardItem('%s' % 'function_switch1'), ])

    def init0tabletableInit(self):
        self.init0model = QStandardItemModel(0, 2)
        self.init0model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.init0table.setModel(self.init0model)
        # 所有列自动拉伸，充满界面
        self.ui.init0table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.init0table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.init0table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.init0table.setEditTriggers(QTableView.NoEditTriggers)
        self.init0model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.init0model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def init1tabletableInit(self):
        self.init1model = QStandardItemModel(0, 2)
        self.init1model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.init1table.setModel(self.init1model)
        # 所有列自动拉伸，充满界面
        self.ui.init1table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.init1table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.init1table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.init1table.setEditTriggers(QTableView.NoEditTriggers)
        self.init1model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.init1model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def init3tabletableInit(self):
        self.init3model = QStandardItemModel(0, 2)
        self.init3model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.init3table.setModel(self.init3model)
        # 所有列自动拉伸，充满界面
        self.ui.init3table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.init3table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.init3table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.init3table.setEditTriggers(QTableView.NoEditTriggers)
        self.init3model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.init3model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def init4tabletableInit(self):
        self.init4model = QStandardItemModel(0, 2)
        self.init4model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.init4table.setModel(self.init4model)
        # 所有列自动拉伸，充满界面
        self.ui.init4table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.init4table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.init4table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.init4table.setEditTriggers(QTableView.NoEditTriggers)
        self.init4model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.init4model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def taraget0tabletableInit(self):
        self.taraget0model = QStandardItemModel(0, 2)
        self.taraget0model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.taraget0table.setModel(self.taraget0model)
        # 所有列自动拉伸，充满界面
        self.ui.taraget0table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.taraget0table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.taraget0table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.taraget0table.setEditTriggers(QTableView.NoEditTriggers)
        self.taraget0model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.taraget0model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def taraget1tabletableInit(self):
        self.taraget1model = QStandardItemModel(0, 2)
        self.taraget1model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.taraget1table.setModel(self.taraget1model)
        # 所有列自动拉伸，充满界面
        self.ui.taraget1table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.taraget1table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.taraget1table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.taraget1table.setEditTriggers(QTableView.NoEditTriggers)
        self.taraget1model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.taraget1model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def taraget3tabletableInit(self):
        self.taraget3model = QStandardItemModel(0, 2)
        self.taraget3model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.taraget3table.setModel(self.taraget3model)
        # 所有列自动拉伸，充满界面
        self.ui.taraget3table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.taraget3table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.taraget3table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.taraget3table.setEditTriggers(QTableView.NoEditTriggers)
        self.taraget3model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.taraget3model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])

    def taraget4tabletableInit(self):
        self.taraget4model = QStandardItemModel(0, 2)
        self.taraget4model.setHorizontalHeaderLabels(['寄存器名', '数据'])
        self.ui.taraget4table.setModel(self.taraget4model)
        # 所有列自动拉伸，充满界面
        self.ui.taraget4table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置只能选中整行
        self.ui.taraget4table.setSelectionMode(QAbstractItemView.SingleSelection)
        # 设置只能选中一行
        self.ui.taraget4table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 不可编辑
        self.ui.taraget4table.setEditTriggers(QTableView.NoEditTriggers)
        self.taraget4model.appendRow([QStandardItem('%s' % 'rx_bytes'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'tx_bytes'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'rx_frames'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'tx_frames'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'rx_signals'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'tx_signals'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'rx_lenerr'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'rx_crcerr'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'Status'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'to_cpu_overflow_cnt'), ])
        self.taraget4model.appendRow([QStandardItem('%s' % 'linking_cnt'), ])


if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QIcon('tech.ico'))
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
