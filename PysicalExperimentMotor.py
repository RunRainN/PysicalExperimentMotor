# -*- coding:utf-8 -*-
import requests
import os
import base64
from bs4 import BeautifulSoup
import re
import time
import lxml.html
import smtplib
from email.mime.text import MIMEText
import hashlib
import getpass


def app_info():
    print("-" * 25)
    print(u"程序名：物理实验小马达")
    print(u"版本：2.4")
    print(u"时间：2019.9")
    print(u"语言：Python 2.7")
    print(u"作者：Run Rain")
    print("-" * 25)


class PhysicalExperimentMotor:
    # 程序初始化
    def __init__(self):
        # 完整的HTTP报头
        self.headers = {
            "Host": "ecpt.cumt.edu.cn",
            "Connection": "keep-alive",
            # "Content-Length": "86",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://ecpt.cumt.edu.cn",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
            # "Content-Type": "application/json",
            # "Referer": "http://ecpt.cumt.edu.cn/index.aspx",
            # "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded"  # 防止post时对data进行url转码
        }
        self.session = requests.session()  # 初始化session对象
        self.experiment_name = {}  # 初始化实验名字典
        self.experiment_time = {}  # 初始化实验时间字典
        self.url = "http://ecpt.cumt.edu.cn/index.aspx"
        try:
            self.html = self.session.get(self.url, headers=self.headers).text  # 获取登录页面
        except Exception as e:
            print(u"连接失败，正在重连...")
            self.__init__()
        self.t = 0  # 用来判断是否是第一次登录

    # 获取用户名和密码
    def get_user_info(self):
        if os.path.exists("user_info"):
            print(u"正在登录...")
            with open("user_info", "r") as f:
                info = f.read()
            self.num = base64.b64decode(info.split()[0])  # 用户信息解密
            self.password = base64.b64decode(info.split()[1])
        else:
            self.t = 1
            print(u"第一次登录初始化")
            print(u"请输入学号："),
            self.num = raw_input()
            self.password = getpass.getpass()
        self.get_captcha()

    # 获取验证码
    def get_captcha(self):
        captcha_url = "http://ecpt.cumt.edu.cn/model/TwoGradePage/VerifyCode.aspx?"
        try:
            captcha = self.session.get(captcha_url, headers=self.headers).content
        except Exception as e:
            print(u"连接失败，正在重连...")
            self.get_captcha()
        with open("captcha.jpeg", "wb") as f:
            f.write(captcha)
        os.startfile("captcha.jpeg")
        print(u"请输入验证码："),
        self.captcha = raw_input()
        self.get_hidden()

    # 获取隐藏POST数据
    def get_hidden(self):
        soup = BeautifulSoup(self.html, "html.parser")
        self.VIEWSTATE = soup.find(id="__VIEWSTATE")["value"]
        self.EVENTVALIDATION = soup.find(id="__EVENTVALIDATION")["value"]
        self.post()

    # 处理data参数并进行post登录
    def post(self):
        data = {
            "ScriptManager1": "login$UpPanel1|login$Btn_Login",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self.VIEWSTATE,
            "__EVENTVALIDATION": self.EVENTVALIDATION,
            "login$txtName": self.num,
            "login$txtPwd": self.password,
            "login$txt_Code": self.captcha,
            "login$Btn_Login": "%E7%99%BB%C2%A0%E5%BD%95"
        }
        self.session.post(self.url, data=data, headers=self.headers)
        center_url = "http://ecpt.cumt.edu.cn/model/Center/stu_acc_grinfo.aspx"
        response = self.session.get(center_url, headers=self.headers)
        # print response.url  #for test
        if response.url == "http://ecpt.cumt.edu.cn/model/Center/stu_acc_grinfo.aspx":
            print(u"\n登录成功！")
            f = open("user_info", "w+")
            f.write(base64.b64encode(self.num))  # 用户信息加密后写入本地
            f.write("\n")
            f.write(base64.b64encode(self.password))
            f.close()
            self.info(response.text)
        else:
            if self.t:
                print(u"用户名或密码或验证码不正确，请重试...")
            else:
                print(u"验证码不正确，请重试...")
            time.sleep(2)
            exit()

    # 获取个人信息
    def info(self, html):
        name_pattern = re.compile('<span id="ctl00_ContentPlaceHolder1_labName">(.*)</span>')
        id_pattern = re.compile('<span id="ctl00_ContentPlaceHolder1_Label2">(.*)</span>')
        class_pattern = re.compile('<span id="ctl00_ContentPlaceHolder1_lbclassname">(.*)</span></td>')
        name = name_pattern.search(html)
        id = id_pattern.search(html)
        stu_class = class_pattern.search(html)
        # print name.group(1), id.group(1), stu_class.group(1)  #for test
        print u"欢迎您，%s！\n" % (name.group(1))
        time.sleep(1)
        print u"=======个人信息======="
        print u"姓名：%s" % (name.group(1))
        print u"学号：%s" % (id.group(1))
        print u"班级：%s" % (stu_class.group(1))
        print ""
        time.sleep(1)
        self.activate(id.group(1), name.group(1))

    # 激活软件
    def activate(self, number, name):
        h = hashlib.md5()  # 创建md5对象
        str = number + name
        h.update(str.encode('utf-8'))
        CDKEY = "CDKEY_" + number  # 激活码文件名
        t = 0
        try:
            f = open(CDKEY, "r")
            text = f.read()
            if text.lower() == h.hexdigest():
                print(u"用户已激活！\n")
                f.close()
                t = 1
        except Exception as reason:
            while True:
                print(u"请输入激活码（请联系作者QQ：1121192423获取）："),
                text = raw_input()
                if text.lower() == h.hexdigest():
                    print(u"激活成功！\n")
                    with open(CDKEY, "w+") as f:
                        f.write(text)
                    time.sleep(1)
                    t = 1
                    break
                else:
                    print(u"激活码不正确，请重新输入")
        if t:
            self.menu()

    # 主菜单
    def menu(self):
        print(u"当前系统时间：%s" % time.ctime())
        print(u"=======功能列表=======")
        print(u"1.实验选课")
        print(u"2.实验余量查询")
        print(u"3.课表查询")
        print(u"4.查看公告栏通知")
        print(u"5.报个Bug/提个建议")
        print(u"6.退出程序")
        # 用户输入判断
        while True:
            try:
                print(u"请选择功能对应的序号："),
                num = int(raw_input())
            except (ValueError, ZeroDivisionError):
                print(u"输入有误，请重新选择")
            else:
                if num < 1 or num > 6:
                    print(u"输入有误，请重新选择")
                else:
                    break
        if num == 1:
            self.item()
        elif num == 2:
            self.number()
        elif num == 3:
            self.schedule()
        elif num == 4:
            self.notice()
        elif num == 5:
            self.advice()
        elif num == 6:
            self.exit()

    # 获取实验信息
    def item(self):
        item_url = "http://ecpt.cumt.edu.cn/model/Center/selectitem.aspx?schoolyearid=36&tblECourseID=360&tblexpplanid=1255&tblPubCourseID=1315"  # 选课网址
        try:
            response = self.session.get(item_url, headers=self.headers)
        except Exception as e:
            print(u"请求超时，请重试...\n")
            self.menu()
        item_html = response.text
        # print item_html  #for test

        # XPath解析
        content = lxml.html.etree.HTML(item_html)
        self.item_list = content.xpath(
            '//tr[@style="background-color:#EFF3FB;height:20px;"]/td[1]/text()') + content.xpath(
            '//tr[@class]/td[1]/text()')
        self.requirement_list = content.xpath(
            '//tr[@style="background-color:#EFF3FB;height:20px;"]/td[2]/font/b/text()') + content.xpath(
            '//tr[@class]/td[2]/font/b/text()')
        self.state_list = content.xpath(
            '//tr[@style="background-color:#EFF3FB;height:20px;"]/td[3]/b/font/text()') + content.xpath(
            '//tr[@class]/td[3]/b/font/text()')
        self.experiment_list()

    # 实验列表及实验选择
    def experiment_list(self):
        n = len(self.item_list)  # 实验总数
        print("%s%20s%30s%25s" % (u"序号", u"项目名称", u"实验要求", u"选课状态"))
        print("-" * 100)
        i = 0
        selected = []
        while n:
            if self.state_list[i] == u"未选":
                print("%d%25s%20s" % (i + 1, self.item_list[i], self.requirement_list[i])),  # print末尾加","打印不换行
                print("%25s" % ("*" + self.state_list[i]))  # 设置“未选”特殊显示
                self.experiment_name.update({i + 1: self.item_list[i]})  # 更新实验名字典
            else:
                print("%d%25s%20s%25s" % (i + 1, self.item_list[i], self.requirement_list[i], self.state_list[i]))
                selected.append(i + 1)  # 记录“已选”对应的序号
            print("-" * 100)
            i += 1
            n -= 1
        print(u"您已选%d个实验" % len(selected))

        # 用户输入判断
        while True:
            t = 1
            try:
                print(u"请选择要选择的实验对应的序号："),
                course_num = int(raw_input())
            except (ValueError, ZeroDivisionError):
                print(u"输入有误，请重新选择")
                t = 0
            else:
                for temp in selected:
                    if course_num == temp or course_num < 1 or course_num > len(self.item_list):
                        print(u"输入有误，请重新选择")
                        t = 0
                        break
            if t:
                break

        while True:
            name = self.experiment_name.get(course_num)
            print(u"您已选择：%s" % name)
            print(u"[Y/N/B](Y:确认进行时间选择\tN:返回重新选择实验\tB:返回主菜单)："),
            judge = raw_input()
            if judge.upper() == "Y":
                self.choose(name)
                break
            elif judge.upper() == "N":
                self.experiment_list()
                break
            elif judge.upper() == "B":
                self.menu()
                break
            else:
                print(u"输入有误，请重新输入")

    # 实验时间选择及发送选课请求
    def choose(self, name):
        experiment_url = {u"实验40 偏振光旋光实验": "241", u"实验27 光的衍射实验": "243", u"实验1 波尔共振仪----受迫振动研究": "245",
                          u"实验14 霍尔效应": "254",
                          u"实验33 光电效应测普朗克常量": "247", u"实验12 高阻直流电势差计的应用": "248", u"实验42 测定铁磁材料的基本磁化曲线和磁滞回线": "249",
                          u"实验31 密立根油滴实验---电子电荷量的测定": "250", u"实验21 数字示波器的使用与信号测量": "252", u"实验28 分光计测三棱镜玻璃折射率": "259",
                          u"实验32 非线性电路中的混沌现象": "253", u"实验18 声速测量": "256", u"实验13 pn结正向特性的研究和应用": "255",
                          u"实验45 太阳能电池的基本特性研究": "257", u"实验30 等厚干涉--牛顿环和劈尖": "251", u"实验22 RC和RL串联电路特性研究": "258",
                          u"实验6 非良导体导热系数的测定": "246", u"实验3 金属线胀系数的测定": "244", u"实验48 磁悬浮导轨碰撞实验": "242",
                          u"实验2 用拉伸法测金属丝的杨氏模量": "213",
                          u"实验26 双棱镜干涉实验": "214", u"实验11 用电势差计测电动势": "215", u"实验19 用电磁感应法测交变磁场": "216",
                          u"实验16 电子在电场、磁场中运动规律的研究": "217", u"实验23 非线性电阻元件伏安特性曲线的测量": "218", u"实验9 双臂电桥测低电阻": "219",
                          u"实验10 交流电桥实验": "220", u"实验8 用模拟法测绘静电场": "221", u"实验24 互感系数的测量实验": "222",
                          u"实验20 电子示波器的使用": "223",
                          u"实验34 弗兰克-赫兹实验": "224", u"实验4 用扭摆法测定物体转动惯量": "225", u"实验15 霍尔效应测螺线管磁场": "226",
                          u"实验47 磁悬浮导轨动力学实验": "227",
                          u"实验39 光的偏振特性研究": "228", u"实验25 迈克耳孙干涉仪": "229", u"实验53 固体密度和液体密度的测量": "230",
                          u"实验29 分光计测光栅常数": "231"}
        data = experiment_url[name.encode('utf-8').decode('utf-8')]
        request_url = "http://ecpt.cumt.edu.cn/model/Center/selectitemtime.aspx?tblKssyxmid=" + data + "&tblexplanid=1255&schoolyearid=36&tblECourseID=360&tblPubCourseID=1315"  # 请求网址
        try:
            response = self.session.get(request_url, headers=self.headers)
        except Exception as e:
            print(u"请求超时,请重试...\n")
            self.menu()
        html = response.content
        content = lxml.html.etree.HTML(html)
        date_list = content.xpath('//tr[@style]/td[2]/text()')
        week_list = content.xpath('//tr[@style]/td[3]/text()')
        week_number_list = content.xpath('//tr[@style]/td[4]/text()')
        time_list = content.xpath('//tr[@style]/td[5]/text()')
        teacher_list = content.xpath('//tr[@style]/td[6]/text()')
        room_list = content.xpath('//tr[@style]/td[7]/text()')
        number_list = content.xpath('//tr[@style]/td[8]/text()')
        number = len(date_list)
        print(
            "%s%10s%20s%20s%10s%20s%20s%20s" % (u"序号", u"日期", u"周次", u"星期", u"节次时间", u"任课教师", u"实验室", u"已选/限选（人）"))
        print('-' * 150)
        option = []
        for i in range(number):
            print("%d%20s%20s%20s%20s%20s%20s%20s" % (
                i + 1, date_list[i], week_list[i], week_number_list[i], time_list[i], teacher_list[i], room_list[i],
                number_list[i]))
            print('-' * 150)
            select = number_list[i].split('/')  # [已选,限选]
            if select[0] != select[1]:
                option.append(i + 1)
        myRadio_list = content.xpath('//td[@style]/input/@value')
        myRadio_dict = {}
        for item1, item2 in zip(option, myRadio_list):
            myRadio_dict.update({item1: item2})
        while True:
            try:
                print(u"请选择序号（输入0则返回主菜单）："),
                num = int(raw_input())
            except (ValueError, ZeroDivisionError):
                print(u"输入有误，请重新选择")
            else:
                if num == 0:
                    self.menu()
                elif num not in option:
                    print(u"选择有误（人数已满的不能选择）")
                    print(u"按回车键重新选择..."),
                    raw_input()
                    self.item()
                break
        myRadio = myRadio_dict[num]
        soup = BeautifulSoup(html, "html.parser")
        EVENTTARGET = soup.find(id="__EVENTTARGET")["value"]
        EVENTARGUMENT = soup.find(id="__EVENTARGUMENT")["value"]
        VIEWSTATE = soup.find(id="__VIEWSTATE")["value"]
        VIEWSTATEGENERATOR = soup.find(id="__VIEWSTATEGENERATOR")["value"]
        VIEWSTATEENCRYPTED = soup.find(id="__VIEWSTATEENCRYPTED")["value"]
        EVENTVALIDATION = soup.find(id="__EVENTVALIDATION")["value"]
        ctl00_HFUserName = soup.find(id="ctl00_HFUserName")["value"]
        ctl00_HFUserID = soup.find(id="ctl00_HFUserID")["value"]
        ctl00_HFUserType = soup.find(id="ctl00_HFUserType")["value"]
        ctl00_HFNodeID = soup.find(id="ctl00_HFNodeID")["value"]
        data = {"ctl00$ContentPlaceHolder1$ctl00": "ctl00$ContentPlaceHolder1$sp|ctl00$ContentPlaceHolder1$btnSave",
                "__EVENTTARGET": EVENTTARGET,
                "__EVENTARGUMENT": EVENTARGUMENT,
                "__VIEWSTATE": VIEWSTATE,
                "__VIEWSTATEGENERATOR": VIEWSTATEGENERATOR,
                "__VIEWSTATEENCRYPTED": VIEWSTATEENCRYPTED,
                "__EVENTVALIDATION": EVENTVALIDATION,
                "myRadio": myRadio,
                "ctl00$HFUserName": ctl00_HFUserName,
                "ctl00$HFUserID": ctl00_HFUserID,
                "ctl00$HFUserType": ctl00_HFUserType,
                "ctl00$HFNodeID": ctl00_HFNodeID,
                "ctl00$ContentPlaceHolder1$btnSave": "%E6%8F%90%E4%BA%A4%E6%95%B0%E6%8D%AE"
                }
        headers = {"Host": "ecpt.cumt.edu.cn",
                   "Connection": "keep-alive",
                   # "Content-Length": "4648",
                   "Cache-Control": "no-cache",
                   "Origin": "http://ecpt.cumt.edu.cn",
                   "X-MicrosoftAjax": "Delta=true",
                   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
                   "Content-Type": "application/x-www-form-urlencoded",
                   "Accept": "*/*",
                   # "Referer": "http://ecpt.cumt.edu.cn/model/Center/selectitemtime.aspx?tblKssyxmid=194&tblexplanid=1255&schoolyearid=36&tblECourseID=360&tblPubCourseID=1315",
                   # "Accept-Encoding": "gzip, deflate",
                   "Accept-Language": "zh-CN,zh;q=0.9"
                   }
        i = 1
        while True:
            print(u"正在进行第%d次尝试，当前系统时间：%s" % (i, time.ctime()))
            try:
                res = self.session.post(request_url, data=data, headers=headers)  # 发送请求
            except Exception as e:
                print(u"请求超时，请重试...\n")
                self.menu()
            html = res.text
            msg = re.compile('"text":"(.*?)"').search(html)
            if html.find(u"成功") != -1:
                print(u"选课成功！")
                print msg.group(1)
                response = self.session.get(request_url, headers=self.headers)
                html = response.content
                content = lxml.html.etree.HTML(html)
                date_list = content.xpath('//tr[@style]/td[2]/text()')
                week_list = content.xpath('//tr[@style]/td[3]/text()')
                week_number_list = content.xpath('//tr[@style]/td[4]/text()')
                time_list = content.xpath('//tr[@style]/td[5]/text()')
                teacher_list = content.xpath('//tr[@style]/td[6]/text()')
                room_list = content.xpath('//tr[@style]/td[7]/text()')
                number_list = content.xpath('//tr[@style]/td[8]/text()')
                number = len(date_list)
                print(
                    "%s%10s%20s%20s%10s%20s%20s%20s" % (
                        u"序号", u"日期", u"周次", u"星期", u"节次时间", u"任课教师", u"实验室", u"已选/限选（人）"))
                print('-' * 150)
                for i in range(number):
                    print("%d%20s%20s%20s%20s%20s%20s%20s" % (
                        i + 1, date_list[i], week_list[i], week_number_list[i], time_list[i], teacher_list[i],
                        room_list[i],
                        number_list[i]))
                    print('-' * 150)
                break
            else:
                print(u"选课失败")
                print msg.group(1)
                print('-' * 100)
                time.sleep(1)
                i += 1
        print(u"按回车键返回主菜单..."),
        raw_input()  # 等待输入，相当于pause
        self.menu()

    # 实验余量查询
    def number(self):
        name_list = [u"实验40 偏振光旋光实验", u"实验48 磁悬浮导轨碰撞实验", u"实验27 光的衍射实验", u"实验3 金属线胀系数的测定", u"实验1 波尔共振仪----受迫振动研究",
                     u"实验6 非良导体导热系数的测定", u"实验33 光电效应测普朗克常量", u"实验12 高阻直流电势差计的应用", u"实验42 测定铁磁材料的基本磁化曲线和磁滞回线",
                     u"实验31 密立根油滴实验---电子电荷量的测定", u"实验30 等厚干涉--牛顿环和劈尖", u"实验32 非线性电路中的混沌现象", u"实验14 霍尔效应",
                     u"实验13 pn结正向特性的研究和应用", u"实验18 声速测量", u"实验45 太阳能电池的基本特性研究", u"实验22 RC和RL串联电路特性研究",
                     u"实验28 分光计测三棱镜玻璃折射率"]
        for data, name in zip(range(241, 260), name_list):
            print name + u"："
            request_url = "http://ecpt.cumt.edu.cn/model/Center/selectitemtime.aspx?tblKssyxmid=" + str(
                data) + "&tblexplanid=1255&schoolyearid=36&tblECourseID=360&tblPubCourseID=1315"  # 请求网址
            try:
                response = self.session.get(request_url, headers=self.headers)
            except Exception as e:
                print(u"请求失败")
                continue
            html = response.content
            content = lxml.html.etree.HTML(html)
            date_list = content.xpath('//tr[@style]/td[2]/text()')
            week_list = content.xpath('//tr[@style]/td[3]/text()')
            week_number_list = content.xpath('//tr[@style]/td[4]/text()')
            time_list = content.xpath('//tr[@style]/td[5]/text()')
            teacher_list = content.xpath('//tr[@style]/td[6]/text()')
            room_list = content.xpath('//tr[@style]/td[7]/text()')
            number_list = content.xpath('//tr[@style]/td[8]/text()')
            number = len(date_list)
            print(
                "%s%10s%20s%20s%10s%20s%20s%20s" % (u"序号", u"日期", u"周次", u"星期", u"节次时间", u"任课教师", u"实验室", u"已选/限选（人）"))
            print('-' * 150)
            for i in range(number):
                select = number_list[i].split('/')  # [已选,限选]
                if select[0] != select[1]:
                    print("%d%20s%20s%20s%20s%20s%20s%20s" % (
                        i + 1, date_list[i], week_list[i], week_number_list[i], time_list[i], teacher_list[i],
                        room_list[i],
                        number_list[i]))
                    print('-' * 150)
            print('\n')
        print(u"按回车键返回主菜单..."),
        raw_input()  # 等待输入，相当于pause
        self.menu()

    # 课表查询
    def schedule(self):
        schedule_url = "http://ecpt.cumt.edu.cn/model/Center/stu_chanxun_myscheduleall.aspx"  # 课表网址
        print(u"正在查询，请稍等..."),
        try:
            response = self.session.get(schedule_url, headers=self.headers)
        except Exception as e:
            print(u"请求超时，请重试...\n")
            self.menu()
        schedule_html = response.text
        # print schedule_html  #for test

        # XPath解析
        content = lxml.html.etree.HTML(schedule_html)
        week_list = content.xpath("//tr[@onmouseover]/td[1]/text()")
        date_list = content.xpath("//tr[@onmouseover]/td[2]/text()")
        time_list = content.xpath("//tr[@onmouseover]/td[3]/text()")
        number_list = content.xpath("//tr[@onmouseover]/td[4]/text()")
        course_list = content.xpath("//tr[@onmouseover]/td[5]/text()")
        item_list = content.xpath("//tr[@onmouseover]/td[6]/text()")
        teacher_list = content.xpath("//tr[@onmouseover]/td[7]/text()")

        place_pattern = re.compile("<td>([A|B]\d\d\d)</td>")  # 使用re避免信息获取不全导致对应错误
        place_list = place_pattern.findall(schedule_html)
        n = len(place_list)
        m = len(week_list)
        print("\n%s%15s%15s%28s%17s%25s%26s%21s" % (u"周次", u"日期", u"时间", u"人数", u"课程", u"项目", u"教师", u"实验室(台位)"))
        print("-" * 180)
        i = 0
        while n:
            print("%s%20s%20s%20s%20s%20s%20s%20s" % (
                week_list[i], date_list[i], time_list[i], number_list[i], course_list[i], item_list[i], teacher_list[i],
                place_list[i]))
            print("-" * 180)
            i += 1
            n -= 1
        print(u"按回车键返回主菜单..."),
        raw_input()  # 等待输入，相当于pause
        self.menu()

    # 查看公告栏通知
    def notice(self):
        response = self.session.get("http://ecpt.cumt.edu.cn/index.aspx", headers=self.headers)
        notice_html = response.text
        content = re.compile('&nbsp;&nbsp;&nbsp; (.*?)</span></span></span>').search(notice_html)
        print("-" * 180)
        print(u"公告栏通知：")
        print content.group(1)
        print("-" * 180)
        print(u"按回车键返回主菜单..."),
        raw_input()  # 等待输入，相当于pause
        self.menu()

    # 发送Bug/建议
    def advice(self):
        msg_from = "1121192423@qq.com"  # 发送方邮箱
        passwd = "xxx"  # 发送方邮箱的授权码（这里已隐藏）
        msg_to = "1121192423@qq.com"  # 收件人邮箱
        subject = "PysicalExperimentMotor_advice"  # 主题
        print(u"请输入Bug或建议："),
        content = raw_input()  # 正文
        print(u"请输入您的联系方式（例如QQ，输入为空则匿名发送）："),
        info = raw_input()
        subject += info
        msg = MIMEText(content)
        msg["Subject"] = subject
        msg["From"] = msg_from
        msg["To"] = msg_to
        try:
            s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
            s.login(msg_from, passwd)
            s.sendmail(msg_from, msg_to, msg.as_string())
            s.quit()
            print(u"发送成功！感谢您的建议")
        except Exception as e:
            print(u"发送失败...")
        finally:
            print(u"按回车键返回主菜单..."),
            raw_input()
            self.menu()

    # 退出程序
    def exit(self):
        print(u"谢谢使用！")
        time.sleep(1)
        exit()


# 程序开始
if __name__ == "__main__":
    app_info()
    motor = PhysicalExperimentMotor()
    motor.get_user_info()
