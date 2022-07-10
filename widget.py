# This Python file uses the following encoding: utf-8
import os
import re
import sys
import time
import random
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from PySide6.QtWidgets import QHeaderView, QAbstractItemView, QTableView
from PySide6.QtCore import QFile, QThread, Signal, Qt, QMutex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtUiTools import QUiLoader
from handledata import HandleData

qmtx = QMutex()


def messageDialog(title, str):
    # 核心功能代码就两行，可以加到需要的地方
    msg_box = QMessageBox(QMessageBox.Warning, title, str)
    msg_box.exec()


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
                time.sleep(5)


class Widget(QWidget):
    def __init__(self):
        self.macconfigflag = False
        self.info = ""
        super(Widget, self).__init__()
        self.load_ui()
        self.ui.smacline.setMaxLength(17)
        self.ui.rmacline.setMaxLength(17)
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
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        self.ui.configbn.clicked.connect(self.configmac)
        ui_file.close()

    def configmac(self):

        self.handleData.send_mac = self.ui.smacline.text()
        if len(self.handleData.send_mac) != 17 or not validate_mac(self.handleData.send_mac):
            messageDialog('警告', 'mac发送地址配置出错！请重试！')
            return
        self.handleData.receive_mac = self.ui.rmacline.text()
        if len(self.handleData.receive_mac) != 17 or not validate_mac(self.handleData.receive_mac):
            messageDialog('警告', 'mac接收地址配置出错！请重试！')
            return
        self.handleData.config_port()
        self.macconfigflag = True
        self.worker.working = True
        messageDialog('成功', 'mac地址配置完成！')

    def updateData(self, data):
        qmtx.lock()
        self.handleData.recievelock.acquire()
        self.handleData.receive_data_content = []
        self.handleData.recievelock.release()
        self.handleData.receive_data(74)
        for v in range(74):
            self.handleData.config_data( "5", "全局配置", "配置请求有效", "写", "是", "00010000", "1200000" + str(random.randint(0, 7)))
            self.handleData.send_data()
        self.handleData.receive_data_process.join()
        for v in range(0, 10):
            index = self.sysregmodel.index(v, 1)
            self.sysregmodel.setData(index,  self.handleData.receive_data_content[v], Qt.DisplayRole)
        for v in range(0,9):
            index = self.init0model.index(v, 1)
            self.init0model.setData(index, self.handleData.receive_data_content[v + 10], Qt.DisplayRole)
        for v in range(0,9):
            index = self.init1model.index(v, 1)
            self.init1model.setData(index, self.handleData.receive_data_content[v + 10], Qt.DisplayRole)
        for v in range(0,9):
            index = self.init3model.index(v, 1)
            self.init3model.setData(index, self.handleData.receive_data_content[v + 10 + 8*1], Qt.DisplayRole)
        for v in range(0,9):
            index = self.init4model.index(v, 1)
            self.init4model.setData(index, self.handleData.receive_data_content[v + 10 + 8*2], Qt.DisplayRole)
        for v in range(0,9):
            index = self.taraget0model.index(v, 1)
            self.taraget0model.setData(index, self.handleData.receive_data_content[v + 10 + 8*3], Qt.DisplayRole)
        for v in range(0,9):
            index = self.taraget1model.index(v, 1)
            self.taraget1model.setData(index, self.handleData.receive_data_content[v + 10 + 8*4], Qt.DisplayRole)
        for v in range(0,9):
            index = self.taraget3model.index(v, 1)
            self.taraget3model.setData(index, self.handleData.receive_data_content[v + 10 + 8*5], Qt.DisplayRole)
        for v in range(0,9):
            index = self.taraget4model.index(v, 1)
            self.taraget4model.setData(index, self.handleData.receive_data_content[v + 10 + 8*6], Qt.DisplayRole)
        qmtx.unlock()

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


if __name__ == "__main__":
    app = QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
