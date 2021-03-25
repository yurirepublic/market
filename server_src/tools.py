"""
脚本管理器的共用工具，抽离出了通信协议之类的

通信协议：
开头 数据长度1024字节 这一段里面用于放所有的控制指令、数据信息
    以utf-8编码，空出来的长度用\0填充
    内容一般是 数据长度（字节）@指令1@指令2@指令3...@end@\0\0\0\0\0\0...

数据 长度写到了开头里面，所以接收足够的字节就停止
    
"""
from io import BufferedIOBase, BufferedWriter
import json
import random
import socket
import _thread
from typing import Tuple, Union, List
import traceback
from multiprocessing import Process, Manager, Lock
import queue
import zipfile
import os
import sys
import time


class ScriptInput(object):
    """
    脚本的输入描述信息\n
    """

    def __init__(self, show_text: str, var_name: str, default):
        self.show_text: str = show_text  # 用于展示给用户的文字，可以是中文
        self.var_name: str = var_name  # 自定义变量名，脚本执行时，会传入字典来接收输入，字典的key就是这名字
        self.default = default  # 展示给用户的时候，默认填充的内容


class ScriptInfo(object):
    """
    脚本的描述信息类\n
    """

    def __init__(self):
        self.title: str = None  # 脚本的标题，和文件名无关，尽量几个字概括功能
        self.description: str = None  # 脚本的描述，可以写长一点，把注意事项什么的全写进去都可以
        self.inputs: list[ScriptInput] = []  # 脚本的输入请求，列表里面放入ScriptInput


class Script(object):
    """
    脚本类，为了让脚本能更好的跑在管理器上（不使用老套的exec去执行）
    同时也是更方便获取脚本状态，以及管理脚本的输出
    甚至是实现脚本说明、输入输出GUI描述
    需要每个脚本都实现一个Script来与管理器对接
    每个脚本都相当于运行在这个类当中
    注意，如果脚本描述信息填写不全，任何一项为None，将不会显示到脚本列表中
    """

    def __init__(self):
        self.log_to_print = False  # 是否在记录log的同时使用print打印出来
        self.manager_dict = None  # 多进程共享字典对象
        self.input_dict = {}  # 初始化用户输入字典

    def run_script(self, manager_dict, input_dict):
        """
        脚本管理器需要调用此函数来运行脚本
        此函数封装了一个异常捕获，使得异常可以写入log
        为了不把manager的传递写入__init__增加用户负担，多进程共享字典也写到了这里
        """
        self.input_dict = input_dict
        self.manager_dict = manager_dict
        self.manager_dict['log'] = '-----开始记录脚本log-----\n'  # 脚本的log
        self.manager_dict['except_exit'] = False  # 是否是因为未捕获的异常而退出
        try:
            self.main()
        except Exception:
            self.log(traceback.format_exc())
            self.manager_dict['except_exit'] = True

    def main(self):
        """
        重写这个函数作为脚本的入口
        不要让脚本管理器调用此函数！！！
        """
        pass

    def info(self) -> ScriptInfo:
        """
        重写此函数作为脚本的描述，需要返回一个ScriptInfo对象
        """
        return ScriptInfo()

    def log(self, *args):
        """
        打印一个log，除非特别设置，否则不会显示到控制台，会打印到脚本的变量中
        如果log_to_time选项为True，会在每条log前面都加上时间
        """
        text = ''
        for e in args:
            text += str(e) + ' '
        if len(args) != 0:
            text = text[:-1]  # 删掉最后一个空格
        time_str = "[" + \
                   time.strftime("%m-%d %H:%M:%S", time.localtime()) + "] "
        self.manager_dict['log'] += time_str + text + '\n'
        if self.log_to_print:
            print(time_str, text)


class BaseHeader(object):
    """
    通信的基础header类
    """

    def __init__(self, length: int, commands: list):
        self.length = length  # 数据长度
        self.commands = commands  # 指令列表


class Base(object):
    """
    通信基础类，依照通信协议提供基本的功能
    """

    def recv_header(self, sock: socket.socket) -> BaseHeader:
        """
        从sock接收一个通信头，返回处理好的数据
        能够保证接收1024个字节
        """
        data = b''
        while len(data) != 1024:
            buf = sock.recv(1024 - len(data))  # 接收剩余的东西
            data += buf
        # 接收完了拿去解析
        data = data.decode('utf-8')
        datas = data.split('@')  # 使用分隔符隔开指令
        datas[0] = int(datas[0])  # 头位一定是数据长度，所以转int
        datas = datas[:-2]  # 数据后两个是end和填充符，直接丢掉
        print(datas)
        header = BaseHeader(datas[0], datas[1:])
        return header

    def recv_ack(self, sock: socket.socket) -> str:
        """
        从sock接收一个确认数据，仅对数据进行字符串解码
        最多接收1024字节
        """
        res = sock.recv(1024).decode('utf-8')
        return res

    def send_ack(self, sock: socket.socket) -> None:
        """
        使用sock发送一个确认数据，数据内容暂时为success的utf-8编码
        """
        sock.send('success'.encode('utf-8'))

    def generate(self, length: int, commands: list) -> bytes:
        """
        传入指令和脚本，生成可以直接发送的字节串
        根据通信协议，会返回1024个字节的通信头
        """
        # 生成文本数据
        res_str = str(length) + '@'
        res_str += '@'.join(commands) + '@end@'
        # 编码
        data = res_str.encode('utf-8')
        # 填充到1024长度
        need_len = 1024 - len(data)
        data += b'\0' * need_len
        return data

    def recv(self, sock: socket.socket, length: int, handler: BufferedIOBase = None) -> Union[bytes]:
        """
        接收指定长度的数据，并写入一个io
        如果io为None，则不写入io，会返回bytes
        """
        if handler is None:
            data = b''
            while length > 0:
                buf = sock.recv(1024)
                length -= len(buf)
                data += buf
            return data
        else:
            while length > 0:
                buf = sock.recv(1024)
                length -= len(buf)
                handler.write(buf)

    def send(self, sock: socket.socket, length: int, handler: BufferedIOBase):
        """
        从一个io读取指定长度数据，并用socket发送出去
        """
        while length > 0:
            buf = handler.read(1024)
            length -= len(buf)
            sock.send(buf)

    def client_ask_data(self, sock: socket.socket, commands: list, io: BufferedIOBase = None) -> Union[bytes]:
        """
        执行一套标准的数据请求流程  用于客户端
        """
        # 生成 & 发送通信头
        header = self.generate(0, commands)
        sock.send(header)

        # 接收数据的通信头
        header = self.recv_header(sock)
        length = header.length

        # 把数据写入io，没有io就返回本地
        data = None
        if io is not None:
            self.recv(sock, length, io)
        else:
            data = self.recv(sock, length)

        # 返回ack信息
        self.send_ack(sock)

        if data is not None:
            return data

    def client_send_data(self, sock: socket.socket, commands: list, data: bytes) -> None:
        """
        执行一套标准的指令附带数据发送流程，暂时只能一次性以bytes形式传入所有data\n
        所以只适用于发送小数据，例如附带的json信息
        :param sock: 套接字
        :param commands: 指令列表
        :param data: 要附带发送数据的bytes
        """
        # 生成 & 发送通信头
        header = self.generate(len(data), commands)
        sock.send(header)

        # 发送数据
        sock.send(data)

        # 接收回执
        self.recv_ack(sock)

    def client_send_command(self, sock: socket.socket, commands: list) -> None:
        """
        执行一套标准的指令发送流程  用于客户端
        和数据请求的区别在于这东西不会接收数据
        """
        # 生成 & 发送通信头
        header = self.generate(0, commands)
        sock.send(header)

        # 接收ack信息
        self.recv_ack(sock)


class ScriptListItem():
    """
    用于服务器存储正在运行脚本列表的类型（这样写方便类型提示）
    """

    def __init__(self, handle: Process, thread_id: int, manager_dict):
        self.handle = handle  # 脚本的进程对象
        self.thread_id = thread_id  # 生成的线程id
        self.manager_dict = manager_dict  # 多进程共享变量的管理器


class Server(Base):
    """
    服务器
    """

    def __init__(self) -> None:
        self.sock: socket.socket = None  # 服务器用于侦听的socket
        self.running_scripts: List[ScriptListItem] = []  # 正在运行的脚本列表
        self._thread_id = 0  # 线程计数器，用于生成不重复的线程id，和threading的ident或者pid不是一回事
        self._thread_id_lock = Lock()  # 线程计数器的多进程锁
        """
        注：脚本的启动实现方式多样化，最开始是threading，现在是Process，以后会什么样子不知道
            所以_thread_id变量的取名仅仅是作为工作的 线程/进程 编号，并不是thread就代表多线程
        """

        # 启动侦听线程
        self.listen_thread = _thread.start_new_thread(self._start_listen, ())

    def _generate_thread_id(self):
        """
        生成不重复的线程识别id
        """
        self._thread_id_lock.acquire()
        res = self._thread_id
        self._thread_id += 1
        self._thread_id_lock.release()
        return res

    def _accept_handler(self, sock: socket.socket, addr: Tuple[int, int]) -> None:
        pid = random.randint(1, 999)
        print('接收到来自%s:%s的请求，分配识别码%d' % (addr[0], addr[1], pid))
        # 接收通信头
        header = self.recv_header(sock)
        # 执行上传指令
        if header.commands[0] == 'upload':
            # 获取要接收的长度
            length = header.length
            # 接收文件
            with open(header.commands[1], 'wb') as f:
                self.recv(sock, length, f)
            # 发送接收完毕的回执
            self.send_ack(sock)
        # 执行下载指令
        elif header.commands[0] == 'download':
            # 先读取文件的字节长度，方便生成消息头
            length = os.path.getsize(header.commands[1])
            # 先将消息头发出去
            sock.send(self.generate(length, []))
            # 再将数据发出去
            with open(header.commands[1], 'rb') as f:
                self.send(sock, length, f)
            # 等客户端发送回执
            response = self.recv_ack(sock)
            print('服务端获得回应', response)
        # 执行ls指令（列出服务器当前目录的文件）
        elif header.commands[0] == 'ls':
            # 获取服务器脚本目录的文件列表，转成json
            data = self._command_ls()
            data = json.dumps(data).encode('utf-8')
            length = len(data)
            # 生成通信头 发送
            header = self.generate(length, [])
            sock.send(header)
            # 把文件list也发出去
            sock.send(data)
            # 等客户端发送回执
            response = self.recv_ack(sock)
            print('获得回应', response)
        elif header.commands[0] == 'exec':
            # 接收附加信息
            data = json.loads(self.recv(sock, header.length).decode('utf-8'))
            self._command_exec(data['script_path'], data['input_dict'])
            print('脚本成功运行')
            # 发送回执
            self.send_ack(sock)
        elif header.commands[0] == 'status':
            data = self._command_status()

            data = json.dumps(data).encode('utf-8')
            length = len(data)
            header = self.generate(length, [])
            sock.send(header)

            sock.send(data)

            response = sock.recv(1024).decode('utf-8')
            print('服务端获得回应', response)
        elif header.commands[0] == 'kill':
            self._command_kill(int(header.commands[1]))
            sock.send('success'.encode('utf-8'))
        elif header.commands[0] == 'clean':
            self._command_clean()
            sock.send('success'.encode('utf-8'))
        elif header.commands[0] == 'get_log':
            # 获取对应的log
            data = self._command_get_log(int(header.commands[1]))
            data = data.encode('utf-8')
            length = len(data)
            # 生成通信头 发送
            header = self.generate(length, [])
            sock.send(header)
            # 把log也发送出去
            sock.send(data)
            # 等客户端发送回执
            response = self.recv_ack(sock)
            print('服务端获得回应', response)

        sock.close()
        print('识别码%d处理完毕' % pid)

    def _command_ls(self) -> list:
        """
        获取脚本目录的脚本列表
        """
        # file_list = os.listdir('scripts')
        file_list = os.listdir('./')
        res = []
        # 将所有文件挨个导入，并检查是否符合规则可以返回
        for e in file_list:
            # 另开进程来避免污染主进程，返回值用manager传递
            def _check_script(file_name, return_dict):
                try:
                    # os.chdir('./scripts')
                    # sys.path.append('./')
                    # 将脚本去掉.py，以模块形式导入
                    script_import = __import__(file_name.replace('.py', ''))
                    # 获取脚本的info信息
                    info: ScriptInfo = script_import.Script().info()
                    # 逐个转录脚本的info信息
                    info_dict = {
                        'title': info.title,
                        'description': info.description,
                        'inputs': []
                    }
                    if None in info_dict.values():
                        raise Exception('主信息不完整', info_dict)
                    for x in info.inputs:
                        temp_dict = {
                            'show_text': x.show_text,
                            'var_name': x.var_name,
                            'default': x.default
                        }
                        if None in temp_dict.values():
                            raise Exception('输入信息不完整', temp_dict)
                        info_dict['inputs'].append(temp_dict)
                    return_dict['return'] = info_dict
                    print('成功识别', file_name)
                except Exception as e:
                    print('识别失败', file_name, e)

            # 启动多进程
            return_manager = Manager().dict()
            handel = Process(target=_check_script, args=(e, return_manager))
            handel.start()
            handel.join()
            # 如果有返回值则直接把返回值丢进结果
            if 'return' in return_manager.keys():
                return_info = return_manager['return']
                return_info['file_name'] = e
                res.append(return_info)
        return res

    def _command_exec(self, script_path: str, input_dict: dict) -> None:
        """
        执行一个服务器上的脚本文件
        :param script_path: 脚本文件名
        :params
        """
        # 生成共享字典对象
        manager_dict = Manager().dict()

        # 执行脚本
        def _x(manager_dict, input_dict, script_path):
            # os.chdir('./scripts')
            # sys.path.append('./')
            # 导入脚本文件的类模块
            script_import = __import__(script_path.replace('.py', ''))
            script = script_import.Script()
            script.run_script(manager_dict, input_dict)

        # script: Script = script_import.Script()
        handle = Process(
            target=_x, args=(manager_dict, input_dict, script_path), name=script_path)
        handle.start()

        # 把脚本丢入正在运行列表中
        self.running_scripts.append(ScriptListItem(
            handle, self._generate_thread_id(), manager_dict))

    def _command_status(self) -> List[Tuple[int, str, str]]:
        """
        获取服务器上脚本运行状态
        返回字典 thread_id, name, status
        """
        res = []
        for e in self.running_scripts:
            status = '运行中' if e.handle.is_alive() else '已结束'
            if e.manager_dict['except_exit']:
                status = '异常结束'
            res.append({
                'thread_id': e.thread_id,
                'name': e.handle.name,
                'status': status
            })
        return res

    def _command_kill(self, thread_id: int) -> None:
        """
        结束掉服务器上某个thread_id的脚本
        """
        for e in self.running_scripts:
            if e.thread_id == thread_id:
                e.handle.kill()
                break

    def _command_get_log(self, thread_id: int) -> str:
        """
        根据thread_id获取某个脚本的log
        """
        log = ''
        for e in self.running_scripts:
            if e.thread_id == thread_id:
                log = e.manager_dict['log']
                break
        return log

    def _command_clean(self) -> None:
        """
        清理掉服务器上已经结束的脚本
        """
        self.running_scripts = list(
            filter(lambda x: x.handle.is_alive(), self.running_scripts))

    def _start_listen(self) -> None:
        """
        开始监听
        """
        # 创建socket
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 设置让程序关闭后立即释放端口
        self.socket.bind((config['script_manager']['server_ip'],
                          config['script_manager']['server_port']))
        self.socket.listen(100)

        print('开始运行脚本管理器服务', config['script_manager']['server_ip'], ':',
              config['script_manager']['server_port'])

        # 开始接收数据
        while True:
            sock, addr = self.socket.accept()
            _thread.start_new_thread(self._accept_handler, (sock, addr))


class Client(Base):
    """
    客户端
    """

    def __init__(self) -> None:
        super().__init__()

    def _create_socket(self) -> socket.socket:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((config['script_manager']['client_ip'],
                   config['script_manager']['client_port']))
        return s

    def upload(self, file_path: str, dst_file_name: str) -> None:
        """
        上传一个文件
        """
        # 获取要上传文件的大小
        length = os.path.getsize(file_path)
        # 发送消息头
        sock = self._create_socket()
        sock.send(self.generate(length, ['upload', dst_file_name]))
        # 发送上传的文件
        with open(file_path, 'rb') as f:
            self.send(sock, length, f)
        # 等待服务器发送接收完毕的回执
        response = self.recv_ack(sock)
        print('客户端获得回应', response)
        sock.close()

    def download(self, file_path: str) -> None:
        """
        从服务器下载一个文件
        """
        sock = self._create_socket()
        with open(file_path, 'wb') as f:
            self.client_ask_data(sock, ['download', file_path], f)
        sock.close()

    def ls(self) -> list:
        """
        列出服务器的文件
        文件列表是json格式，使用utf-8编码放在数据部分
        """
        sock = self._create_socket()
        response = self.client_ask_data(sock, ['ls'])
        response = json.loads(response)
        sock.close()

        return response

    def status(self) -> dict:
        """
        列出服务器上运行的脚本
        """
        sock = self._create_socket()
        response = self.client_ask_data(sock, ['status'])
        response = json.loads(response)
        sock.close()

        return response

    def kill(self, thread_id: int) -> None:
        """
        终止某个服务器上运行的脚本
        """

        sock = self._create_socket()
        self.client_send_command(sock, ['kill', str(thread_id)])
        sock.close()

    def get_log(self, thread_id: int) -> str:
        """
        获取某个thread_id脚本的log信息
        """
        sock = self._create_socket()
        response = self.client_ask_data(sock, ['get_log', str(thread_id)])
        response = response.decode('utf-8')
        sock.close()

        return response

    def clean(self) -> None:
        """
        清理服务器上已终止运行的脚本
        """

        sock = self._create_socket()
        self.client_send_command(sock, ['clean'])
        sock.close()

    def exec(self, script_path: str, input_dict: dict) -> None:
        """
        执行服务器上某个脚本
        """
        sock = self._create_socket()
        data = {
            'script_path': script_path,
            'input_dict': input_dict,
        }
        data = json.dumps(data).encode('utf-8')
        header = self.generate(len(data), ['exec'])
        # 发出header
        sock.send(header)
        # 发出data
        sock.send(data)
        # 接收回执
        self.recv_ack(sock)

        sock.close()
