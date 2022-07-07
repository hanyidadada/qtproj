import os
import re
import random
import binascii
import psutil
from scapy.all import sniff, sendp, Ether, raw
# from err_up_package import ErrUpPackage
# from err_down_package import ErrDownPackage
import datetime
import time


class HandleData:
    def __init__(self):
        self.printflag = False
        self.logflag = False
        self.macflag = False
        self.receive_data_content = ""
#        self.send_mac = "88:a4:c2:98:c3:99"
#        self.receive_mac = "00:0c:29:0c:38:8a"
        self.send_mac = ""
        self.receive_mac = ""
        self.data_content = ""
        self.analyze_data_content = ""

    def analyze_data(self):
        self.analyze_data_content = self.receive_data_content
        self.analyze_data_content = self.analyze_data_content.replace(' ', '')
        self.analyze_data_content = self.analyze_data_content[32:]
        if self.printflag:
            print(self.analyze_data_content)

        # 接下来需要解析数据
        # 数据包长度(4Byte)
        config_len = self.analyze_data_content[0:2]
        if self.printflag:
            print("0x" +config_len)
        # 防止收到的包过长
        self.analyze_data_content = self.analyze_data_content[0:8*int(config_len)]
        # 配置包的方向为)
        config_channel = '{:016b}'.format(int(self.analyze_data_content[4:8], 16))
        config_channel = config_channel[6:9]
        if config_channel == "100":
            config_channel_text = "全局配置"
        elif config_channel == "101":
            config_channel_text = "tcam配置"
        else:
            config_channel_text = "其他配置"
        if self.printflag:
            print(config_channel_text)

        # 32位随机值为
        config_id = self.analyze_data_content[8:16]
        config_id = re.sub(r"(?<=\w)(?=(?:\w\w)+$)", " ", config_id)
        if self.printflag:
            print(config_id)

        config_rwcr = '{:04b}'.format(int(self.analyze_data_content[16], 16))

        # 配置请求为
        if config_rwcr[0] == "1":
            config_req = "配置请求有效"
        else:
            config_req = "配置请求无效"
        if self.printflag:
            print(config_req)

        # 读写状态为
        if config_rwcr[1] == "1":
            config_write_read = "写"
        else:
            config_write_read = "读"
        if self.printflag:
            print(config_write_read)

        # 读清零标志为
        if config_rwcr[2] == "1":
            config_clr = "是"
        else:
            config_clr = "否"
        if self.printflag:
            print(config_clr)

        # 全局地址为
        global_addr = self.analyze_data_content[17:24]
        global_addr = re.sub(r"(?<=\w)(?=(?:\w\w)+$)", " ", global_addr)
        if self.printflag:
            print(global_addr.replace(" ", ""))

        # 配置内容为
        config_data = ""
        config_data = self.analyze_data_content[24:-8]
        config_data = re.sub(r"(?<=\w)(?=(?:\w\w)+$)", " ", config_data)
        if self.printflag:
            print(config_data.replace(" ", ""))

        last_data = '{:032b}'.format(int(self.analyze_data_content[-8:], 16))

        # config_err为
        if last_data[-4:] == "0000":
            config_err = "正确，无错误"
        elif last_data[-4:] == "0001":
            config_err = "非配置包"
        elif last_data[-4:] == "0010":
            config_err = "配置通道错误"
        elif last_data[-4:] == "0011":
            config_err = "配置类型错误"
        elif last_data[-4:] == "0100":
            config_err = "结束符错误"
        elif last_data[-4:] == "0101":
            config_err = "删除配置表项失败"
        else:
            config_err = "解析失败"
        if self.printflag:
            print(config_err)

        # 查到的规则索引号为
        config_look_hit_idx = last_data[12:28]
        config_look_hit_idx = hex(int(config_look_hit_idx, 2))[2:].zfill(4)
        config_look_hit_idx = re.sub(
            r"(?<=\w)(?=(?:\w\w)+$)", " ", config_look_hit_idx)
        if self.printflag:
            print(config_look_hit_idx)

        return config_data.replace(" ", "")

    def send_data(self):
        send_addr = self.send_mac.upper().replace(':', '')
        receive_addr = self.receive_mac.upper().replace(':', '')
        ethernet = Ether(dst=self.receive_mac,
                         src=self.send_mac, type=0xA000)
        portname = ""
        for k, v in psutil.net_if_addrs().items():
            for item in v:
                address = item[1]
                if os.name == 'posix':
                    if ":" in address and len(address)==17 and self.send_mac.upper().replace('-', ':') == address.upper():
                        portname = k
                else:
                    if "-" in address and len(address)==17 and self.send_mac.upper().replace('-', ':') == address.upper():
                        portname = k

        res16 = bytes.fromhex("0000")
        payload = self.data_content
        # raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0xA000))
        # raw_socket.bind((socket.gethostname(), 0))
        # crc32 = crcmod.predefined.mkCrcFun('CRC-32')
        # crc_check = bytes.fromhex('{:08x}'.format(crc32(receive_addr+send_addr+proto+res16+payload)))
        crc_check_bw = "%08x" % (binascii.crc32(binascii.a2b_hex(
            receive_addr+send_addr+"A0000000"+payload)) & 0xffffffff)
        crc_check = crc_check_bw[6:8] + crc_check_bw[4:6] + \
            crc_check_bw[2:4] + crc_check_bw[0:2]
        payload = bytes.fromhex(payload)
        crc_check = bytes.fromhex(crc_check)
        package = ethernet/res16/payload/crc_check
        sendp(package, iface=portname)
        filter_rule = "ether proto 0xa001"
        if self.printflag:
            print(filter_rule)
        sniff(count=1, iface=portname, filter=filter_rule, prn=self.show)
        if self.printflag:
            print("stop sniff")
        time.sleep(0.06)

    def config_data(self, configlen, configchannel, configreq, configwr, configclr, configaddr, configcontent):
        self.config_len = configlen
        self.config_channel = configchannel
        self.config_req = configreq
        self.config_write_read = configwr
        self.config_clr = configclr
        self.config_addr = configaddr
        self.config_content = configcontent
        self.get_data()

    def get_data(self):
        # 生成一个8位长的数据包长度信息
        len_byte = self.config_len
        binary_len_byte = '{:08b}'.format(int(len_byte))

        # 生成一个3位长度的配置包方向信息
        channel = self.config_channel
        if channel == "全局配置":
            binary_channel = "100"
        elif channel == "tcam配置":
            binary_channel = "101"
        else:
            binary_channel = "000"

        # 生成一个1位长度的req消息
        req = self.config_req
        if req == "配置请求有效":
            binary_req = "1"
        else:
            binary_req = "0"

        # 生成一个1位长度的w/r消息
        write_read = self.config_write_read
        if write_read == "写":
            binary_write_read = "1"
        else:
            binary_write_read = "0"

        # 生成一个1位长度的clr消息
        clr = self.config_clr
        if clr == "是":
            binary_clr = "1"
        else:
            binary_clr = "0"

        # 生成一个28位长度的全局地址
        global_addr = self.config_addr
        global_addr = int(global_addr.upper().replace(' ', ''), 16)
        binary_global_addr = '{:028b}'.format(global_addr)

        # 生成一个符合len_byte长度的数据部分
        content = self.config_content
        length_content = len(content.replace(' ', '')) * 4
        content = int(content.upper().replace(' ', ''), 16)
        data_len = (int(len_byte) - 4) * 32
        binary_content = '{:0{}b}'.format(content, length_content)
        binary_content = binary_content.ljust(data_len, "0")
        # 定义一些其它的数据
        binary_res14 = "00000000000000"
        binary_res6 = "000000"
        binary_cfg = "0"
        binary_res1 = "0"
        binary_res12 = "000000000000"
        binary_look_hit_idx = "0000000000000000"
        binary_config_err = "0000"
        seed = "01"
        sa = []
        for i in range(0, 32):
            sa.append(random.choice(seed))
        binary_config_id = "".join(sa)

        binary_data = binary_len_byte + binary_res14 + binary_channel + binary_res6 + binary_cfg + \
            binary_config_id + binary_req + binary_write_read + binary_clr + binary_res1 + \
            binary_global_addr + binary_content + binary_res12 + \
            binary_look_hit_idx + binary_config_err
        len_content = int(len_byte) * 8
        # self.hex_data = hex(int(binary_data, 2))[2:]
        hex_data = '{:0{}x}'.format(int(binary_data, 2), len_content)
        self.data_content = ""
        self.data_content = hex_data

    # 接收到数据包后进行数据存储
    def show(self, p):
        if self.printflag:
            p.show()
        come_back_hex = eval(str(raw(p)))
        come_back = come_back_hex.hex()
        self.receive_data_content = come_back
        if self.logflag:
            with open('receive_data_log.txt', 'a') as f1:
                f1.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+ " " +come_back + '\n')
                f1.close()


if __name__ == '__main__':
    handle = HandleData()
    t1 = time.time()
    handle.logflag = True

    for v in range(75) :
        handle.config_data( "5", "全局配置", "配置请求有效", "写", "是", "00010000", "12000000")
        # t2 = time.time()
        # print("配置数据时间：" + str((t2-t1)*1000))
        handle.send_data()
        # t3 = time.time()
        # print("收发数据时间：" + str((t3-t1)*1000))
        ret = handle.analyze_data()
        # t4 = time.time()
        # print("分析数据时间：" + str((t4-t1)*1000))
        # print(ret)
    t5 = time.time()
    print("总时间：" + str((t5-t1)*1000))
    # handle.config_data( "5", "全局配置", "配置请求有效", "写", "是", "00010000", "12000022")
    # handle.send_data()
    # ret = handle.analyze_data()
    # print(ret)
