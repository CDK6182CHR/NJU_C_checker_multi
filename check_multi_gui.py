"""
UTF-8编码的文本文档来记录程序运行数据。每次确认都记录数据。数据格式类似csv：
文件夹全名,题号,得分,批注。
todo 最后一个文件夹后按提交没有自动进入下一个文件夹
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys,os,re
from popenThread import PopenThread
from preProcessing import pre_code
from datetime import datetime


class checkWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super().__init__()
        self.setWindowTitle("C语言作业批改系统  V0.1")
        self.workDir = '.'
        self.examples = []
        self.popenThread = None
        self.log_file = None
        self.initUI()

    def initUI(self):
        self.initCentral()
        self.initToolBar()
        self.initFileDock()
        self.initDirDock()
        self.initExamplesDock()
        self.initCurrentExampleDock()

    def initCentral(self):
        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()

        btnCheck = QtWidgets.QPushButton('测试(&T)')
        btnNext = QtWidgets.QPushButton('提交(&S)')
        btn3 = QtWidgets.QPushButton('3分(&3)')
        btn2 = QtWidgets.QPushButton('2分(&2)')
        btn1 = QtWidgets.QPushButton('1分(&1)')
        btn0 = QtWidgets.QPushButton('0分(&0)')
        btnUnknown = QtWidgets.QPushButton('待定(&U)')

        btnCheck.clicked.connect(lambda:self.checkAProblem(self.dirListWidget.currentItem().text(),
                                                           self.exampleList.currentItem().data(-1)))
        btnNext.clicked.connect(self.next_clicked)
        btn3.clicked.connect(lambda:self.mark_btn_clicked(3))
        btn2.clicked.connect(lambda:self.mark_btn_clicked(2))
        btn1.clicked.connect(lambda:self.mark_btn_clicked(1))
        btn0.clicked.connect(lambda:self.mark_btn_clicked(0))
        btnUnknown.clicked.connect(lambda:self.mark_btn_clicked(-1))

        line = QtWidgets.QLineEdit()
        self.markLine = line
        line.setMaximumWidth(80)

        hlayout.addWidget(btnNext)
        hlayout.addWidget(btnCheck)
        label = QtWidgets.QLabel('得分(&M)')
        label.setBuddy(line)
        hlayout.addWidget(label)
        hlayout.addWidget(line)
        hlayout.addWidget(btn3)
        hlayout.addWidget(btn2)
        hlayout.addWidget(btn1)
        hlayout.addWidget(btn0)
        hlayout.addWidget(btnUnknown)

        note = QtWidgets.QLineEdit()
        self.noteLine = note
        label = QtWidgets.QLabel("批注(&N)")
        label.setBuddy(note)
        hlayout.addWidget(label)
        hlayout.addWidget(note)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        btnTerminate = QtWidgets.QPushButton('中止(&A)')
        btnTerminate.clicked.connect(self.terminate_test)
        hlayout.addWidget(btnTerminate)

        hlayout.addWidget(QtWidgets.QLabel("当前题号"))
        
        numberEdit = QtWidgets.QLineEdit()
        self.numberEdit = numberEdit
        hlayout.addWidget(numberEdit)

        fileEdit = QtWidgets.QLineEdit()
        self.fileEdit = fileEdit
        hlayout.addWidget(QtWidgets.QLabel("当前文件名"))
        hlayout.addWidget(fileEdit)
        layout.addLayout(hlayout)
        
        hlayout = QtWidgets.QHBoxLayout()
        outEdit = QtWidgets.QTextEdit()
        self.outEdit = outEdit
        hlayout.addWidget(outEdit)

        from highLight import PythonHighlighter,TextEdit
        codeEdit = TextEdit()
        self.codeEdit = codeEdit
        hlayout.addWidget(codeEdit)
        highLighter = PythonHighlighter(codeEdit.document())


        layout.addLayout(hlayout)
        widget.setLayout(layout)

    def initToolBar(self):
        toolBar = QtWidgets.QToolBar(self)
        dirEdit = QtWidgets.QLineEdit()
        dirEdit.setText(self.workDir)

        self.dirEdit = dirEdit
        label = QtWidgets.QLabel('工作路径(&C)')
        label.setBuddy(dirEdit)
        toolBar.addWidget(label)
        toolBar.addWidget(dirEdit)
        btnRefresh = QtWidgets.QPushButton("刷新工作区(&R)",self)
        btnRefresh.clicked.connect(self.refresh_workdir)
        dirEdit.editingFinished.connect(btnRefresh.click)
        toolBar.addWidget(btnRefresh)

        btnNextDir = QtWidgets.QPushButton("下一文件夹(&D)")
        btnNextDir.clicked.connect(self.next_dir)
        self.btnNextDir = btnNextDir
        toolBar.addWidget(btnNextDir)

        self.addToolBar(toolBar)
    
    def initFileDock(self):
        """
        当前工作区下文件表
        """
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("工作区文件夹")
        self.fileDock = dock

        listWidget = QtWidgets.QListWidget()
        self.fileListWidget = listWidget
        dock.setWidget(listWidget)
        listWidget.currentItemChanged.connect(self.dir_changed)

        self.addDockWidget(Qt.LeftDockWidgetArea,dock)

    def initDirDock(self):
        """
        批改的作业文件夹
        """
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("当前作业文件夹")

        listWidget = QtWidgets.QListWidget()
        dock.setWidget(listWidget)
        self.dirListWidget = listWidget
        listWidget.currentItemChanged.connect(self.dir_line_changed)

        self.addDockWidget(Qt.LeftDockWidgetArea,dock)

    def initExamplesDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle('测试用例表')

        listWidget = QtWidgets.QListWidget()
        listWidget.currentItemChanged.connect(self.example_changed)
        self.exampleList = listWidget
        dock.setWidget(listWidget)
        self.addDockWidget(Qt.RightDockWidgetArea,dock)

    def initCurrentExampleDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("本题目测试用例")

        textEdit = QtWidgets.QTextEdit()
        dock.setWidget(textEdit)
        self.exampleEdit = textEdit

        self.addDockWidget(Qt.RightDockWidgetArea,dock)

    def getExamples(self):
        """
        从当前工作区下自动读取测试用例。文件名格式为  题号_测试用例编号.txt。
        """
        self.examples.clear()
        try:
            os.chdir('inputs')
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误',
            '找不到测试用例文件：请将测试用例放在工作区根目录的inputs文件夹下。\n'+repr(e))
            return
        
        unaccepted_files = []
        for t in os.scandir('.'):
            nums = list(map(int,re.findall('(\d+)',t.name)))
            if len(nums) >= 1 and not t.is_dir():
                try:
                    self.examples[nums[0]].append(t.name)
                except:
                    while len(self.examples) <= nums[0]:
                        self.examples.append([])
                    self.examples[nums[0]].append(t.name)
        self.examples.remove([])
        print("测试用例表",self.examples)
        os.chdir('..')
        self.exampleList.clear()
        for a in self.examples:
            item = QtWidgets.QListWidgetItem()
            item.setData(-1,a)
            item.setText(';'.join(a))
            self.exampleList.addItem(item)

    def loadDir(self,dir_name):
        """
        更新切换当前作业dir，初始化listWidget。
        """
        code_dir = None
        os.chdir(self.workDir)
        os.chdir(dir_name)
        self.dirListWidget.clear()
        for a,b,c in os.walk('.'):
            for t in c:
                if '.c'in t or '.C' in t:
                    code_dir = a
                    break
            if code_dir is not None:
                break
        for t in os.scandir(code_dir):
            if not t.is_dir() and ('.c' in t.name or '.C' in t.name) and '.exe' not in t.name:
                filename = "{}\\{}".format(code_dir,t.name)
                self.dirListWidget.addItem(filename)
        if self.dirListWidget.count():
            self.dirListWidget.setCurrentRow(0)
        else:
            QtWidgets.QMessageBox.warning("找不到源文件！")


    # slots
    def mark_btn_clicked(self,marks:int):
        if marks != -1:
            self.markLine.setText(str(marks))
        else:
            self.markLine.setText('待定')

    def next_clicked(self):
        """
        下一题
        """
        # 先提交上一题的更改
        with open(self.log_file,'a',encoding='utf-8',errors='ignore') as fp:
            # 文件夹全名，题号，得分，批注
            note = f'{self.fileListWidget.currentItem().text()},'\
                     f'{self.numberEdit.text()},'\
                     f'{self.markLine.text()},'\
                     f'{self.noteLine.text()}'
            fp.write(note+'\n')
            self.statusBar().showMessage(f"{datetime.now().strftime('%H:%M:%S')} 写入记录：{note}")
        idx = self.dirListWidget.currentRow()
        if idx < self.dirListWidget.count():
            self.dirListWidget.setCurrentRow(self.dirListWidget.currentRow()+1)
        else:
            self.statusBar().showMessage(f'{datetime.now().strftime("%H:%M:%S")}'
                                         f'最后一个文件，自动进入下一个文件夹。')
            self.btnNextDir.click()
        self.noteLine.setText('')
        self.markLine.setText('3')

    def refresh_workdir(self):
        """
        扫描当前工作区，初始化listWidget
        """
        self.workDir = self.dirEdit.text()
        self.fileListWidget.clear()
        self.workDir.rstrip('\\')
        self.workDir.rstrip('/')
        try:
            os.chdir(self.workDir)
            for t in os.scandir(self.workDir):
                if t.is_dir() and t.name not in ('__pycache__','inputs'):
                    self.fileListWidget.addItem(t.name)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','文件夹非法\n'+repr(e))
            return
        self.log_file = self.workDir+'\\log.txt'
        with open(self.log_file,'a',encoding='utf-8',errors='ignore') as fp:
            fp.write(f'//打开时间：{datetime.now().strftime("%y-%m-%d %H:%M:%S")}\n')
        self.getExamples()

    def checkAProblem(self,source:str,examples:list):
        """
        检查一道题，将结果输出到outEdit中。
        """
        note = pre_code(source)
        self.outEdit.setText(note)
        compile_cmd = f'gcc "{source}" -o "{source}.exe" --std=c99'
        out = os.popen(compile_cmd)
        self.outEdit.setText('*************编译输出*************\n'+out.read()+'\n\n')

        popenThread = PopenThread(source,self.workDir,examples)
        self.popenThread = popenThread
        popenThread.CheckFinished.connect(self.check_finished)
        popenThread.AllFinished.connect(self.check_all_finished)
        popenThread.start()

    # slots
    def check_finished(self,example,output_str):
        self.outEdit.setText(self.outEdit.toPlainText()
                             + f'\n\n---------测试用例 {example}---------\n' + output_str)

    def check_all_finished(self):
        self.outEdit.setText(self.outEdit.toPlainText()
                             + '\n\n===========测试正常结束===========\n')

    def next_dir(self):
        listWidget = self.fileListWidget
        if listWidget.currentRow() < listWidget.count():
            listWidget.setCurrentRow(listWidget.currentRow()+1)
        else:
            QtWidgets.QMessageBox.information(self,'提示','已经是最后一个文件！')
            return

    def dir_changed(self,item:QtWidgets.QListWidgetItem):
        """
        由fileListWidget切换触发。
        """
        if item is not None:
            self.loadDir(item.text())

    def dir_line_changed(self,item:QtWidgets.QListWidgetItem):
        """
        由dirListWidget切换触发。
        """
        if item is None:
            return
        idx = self.dirListWidget.currentRow()
        try:
            examples = self.examples[idx]
        except IndexError:
            QtWidgets.QMessageBox.information(self,'提示',
                                              '没有顺序匹配的测试用例，请手动选择测试用例并进行测试')
        else:
            self.exampleList.setCurrentRow(idx)
            self.checkAProblem(item.text(),examples)
        try:
            with open(item.text(),'r',encoding='GBK',errors='ignore') as fp:
                self.codeEdit.setText(fp.read())
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','文件错误\n'+repr(e))
        self.fileEdit.setText(item.text())
        self.numberEdit.setText(str(idx+1))

    def example_changed(self,item:QtWidgets.QListWidgetItem):
        example_contents = []
        example_files = item.data(-1)
        for f in example_files:
            with open(self.workDir+'\\inputs\\'+f,errors='ignore') as fp:
                example_contents.append(f+'\n'+fp.read())
        self.exampleEdit.setText('\n\n====================\n'.join(example_contents))

    def terminate_test(self):
        if self.popenThread is not None:
            self.popenThread.terminate()
            self.outEdit.setText(self.outEdit.toPlainText()+'\n\n##########\n测试中止\n##########')

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = checkWindow()
    w.showMaximized()
    app.exec_()