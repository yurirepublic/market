from typing import Tuple, Union, List, Dict
import traceback
from multiprocessing import Process, Manager, Lock
import os
import time
import asyncio
import data_center
import json


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
        self.inputs: List[ScriptInput] = []  # 脚本的输入请求，列表里面放入ScriptInput


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
            exit(0)
        except KeyboardInterrupt:
            exit(0)

    def main(self):
        """
        重写这个函数作为脚本的入口
        不要让脚本管理器调用此函数！！！
        """
        pass

    @staticmethod
    def info() -> ScriptInfo:
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


class ScriptListItem(object):
    """
    用于服务器存储正在运行脚本列表的类型（这样写方便类型提示）
    """

    def __init__(self, handle: Process, thread_id: int, manager_dict):
        self.handle = handle  # 脚本的进程对象
        self.thread_id = thread_id  # 生成的线程id
        self.manager_dict = manager_dict  # 多进程共享变量的管理器


class Core(object):
    """
    脚本管理器内核
    """

    def __init__(self, loop) -> None:
        self.running_scripts: List[ScriptListItem] = []  # 正在运行的脚本列表
        self._thread_id = 0  # 线程计数器，用于生成不重复的线程id，和threading的ident或者pid不是一回事
        self._thread_id_lock = Lock()  # 线程计数器的多进程锁
        """
        注：脚本的启动实现方式多样化，最开始是threading，现在是Process，以后会什么样子不知道
            所以_thread_id变量的取名仅仅是作为工作的 线程/进程 编号，并不是thread就代表多线程3
        """
        self.loop = loop
        self.loop.create_task(self.running_status_observer())

    async def running_status_observer(self):
        """
        此协程监控脚本的运行状况
        """
        ws = await data_center.create_client()
        while True:
            await ws.update({'json', 'scriptManager', 'status'}, json.dumps(self.status()))
            await asyncio.sleep(3)

    def _generate_thread_id(self):
        """
        生成不重复的线程识别id
        """
        self._thread_id_lock.acquire()
        res = self._thread_id
        self._thread_id += 1
        if self._thread_id > 1000000:
            self._thread_id = 0
        self._thread_id_lock.release()
        return res

    @staticmethod
    def ls() -> list:
        """
        获取脚本目录的脚本列表
        """
        # file_list = os.listdir('scripts')
        file_list = os.listdir('./')
        res = []
        # 将所有文件挨个导入，并检查是否符合规则可以返回
        for e in file_list:
            # 只对名字前缀为sc_的文件进行扫描
            if e.find('sc_') != 0:
                continue

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
                except Exception as _e:
                    print('识别失败', file_name, _e)

            # 启动多进程
            return_manager = Manager().dict()
            handle = Process(target=_check_script, args=(e, return_manager))
            handle.start()
            handle.join()
            # 如果有返回值则直接把返回值丢进结果
            if 'return' in return_manager.keys():
                return_info = return_manager['return']
                return_info['file_name'] = e
                res.append(return_info)
        return res

    def exec(self, script_path: str, input_dict: dict) -> None:
        """
        执行一个服务器上的脚本文件
        :param script_path: 脚本文件名
        :param input_dict: 运行脚本的写入参数
        """
        # 生成共享字典对象
        manager_dict = Manager().dict()

        # 执行脚本
        def _x(_manager_dict, _input_dict, _script_path):
            # os.chdir('./scripts')
            # sys.path.append('./')
            # 导入脚本文件的类模块
            script_import = __import__(_script_path.replace('.py', ''))
            script = script_import.Script()
            script.run_script(_manager_dict, _input_dict)

        # script: Script = script_import.Script()
        handle = Process(
            target=_x, args=(manager_dict, input_dict, script_path), name=script_path)
        handle.start()

        # 把脚本丢入正在运行列表中
        self.running_scripts.append(ScriptListItem(
            handle, self._generate_thread_id(), manager_dict))

    def status(self) -> List[Dict]:
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

    def kill(self, thread_id: int) -> None:
        """
        结束掉服务器上某个thread_id的脚本
        """
        for e in self.running_scripts:
            if e.thread_id == thread_id:
                e.handle.kill()
                break

    def kill_all(self):
        """
        结束掉服务器上所有的脚本
        """
        for e in self.running_scripts:
            e.handle.kill()

    def get_log(self, thread_id: int) -> str:
        """
        根据thread_id获取某个脚本的log
        """
        log = ''
        for e in self.running_scripts:
            if e.thread_id == thread_id:
                log = e.manager_dict['log']
                break
        return log

    def clean(self) -> None:
        """
        清理掉服务器上已经结束的脚本
        """
        self.running_scripts = list(
            filter(lambda x: x.handle.is_alive(), self.running_scripts))