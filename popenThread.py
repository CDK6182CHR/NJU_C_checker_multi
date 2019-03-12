"""
用于执行命令的线程。只执行程序并写入输出内容，程序应该已经编译完毕。
"""
from PyQt5.QtCore import QThread,pyqtSignal,QProcess,QByteArray
from PyQt5.QtWidgets import QMessageBox
import os,re
from preProcessing import shell_cmd,run_cmd,read_out

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
            self.example = example
            example_file = self.workDir + '\\inputs\\'+example
            cmd_single = run_cmd(self.source,example_file)
            self.cmd = cmd_single
            cmd = shell_cmd(cmd_single)
            p = QProcess()
            self.process = p
            p.start('cmd')
            p.waitForStarted(1000)
            p.write(bytes(cmd,'GBK'))
            p.closeWriteChannel()
            p.waitForFinished()
            output = p.readAllStandardOutput()
            # print("output is",output)
            self.CheckFinished.emit(example,read_out(output,cmd_single))
        self.AllFinished.emit()

    def terminate(self):
        back = '\\'
        cmd = f'taskkill /f /im "{self.source.split(back)[-1]}.exe" '
        out = os.popen(cmd)
        try:
            self.CheckFinished.emit('',out.read())
        except Exception as e:
            print("emit failed",repr(e))
        self.CheckFinished.emit(self.example,read_out(self.process.readAll(),self.cmd))
        self.process.terminate()
        super().terminate()
