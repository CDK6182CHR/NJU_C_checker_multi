"""
用于执行命令的线程。只执行程序并写入输出内容，程序应该已经编译完毕。
"""
from PyQt5.QtCore import QThread,pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import os

class PopenThread(QThread):
    CheckFinished = pyqtSignal(str,str)
    AllFinished = pyqtSignal()
    def __init__(self,source:str,workDir:str,examples:list):
        super().__init__()
        self.examples = examples
        self.workDir = workDir
        self.source = source
        self.cur = None

    def run(self):
        for example in self.examples:
            print(example)
            example_file = self.workDir + '\\inputs\\'+example
            cmd = f'"{self.source}.exe" < "{example_file}"'
            self.cur = os.popen(cmd)
            output=self.cur
            try:
                output_str = output.read()
            except Exception as e:
                output_str = '执行错误\n'+repr(e)

            self.CheckFinished.emit(example,output_str)
        self.AllFinished.emit()

    def terminate(self):
        try:
            self.cur.close()
        except:
            pass
        super().terminate()
