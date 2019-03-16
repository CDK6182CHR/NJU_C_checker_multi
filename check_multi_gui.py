"""
UTF-8编码的文本文档来记录程序运行数据。每次确认都记录数据。数据格式类似csv：
文件夹全名,源文件名,批改时间,题号,得分,批注。
"""

from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import Qt
import sys,os,re
from popenThread import PopenThread
from preProcessing import pre_code,shell_cmd,read_out,compile_cmd
from datetime import datetime
from highlighter import HighLighter

import cgitb
cgitb.enable(format='text')

class checkWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super().__init__()
        self.name = '南京大学C语言作业批改系统'
        self.version = 'V1.1.3'
        self.date = '20190316'
        self.setWindowTitle(f"{self.name} {self.version}")
        self.workDir = '.'
        self.examples = []
        self.fastNotes = []
        self.popenThread = None
        self.log_file = None
        self.initUI()

    def initUI(self):
        self.initCentral()
        self.initFileDock()
        self.initDirDock()
        self.initExamplesDock()
        self.initCurrentExampleDock()
        self.initToolBar()

    def initCentral(self):
        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()

        btnCheck = QtWidgets.QPushButton('测试(&T)')
        btnNext = QtWidgets.QPushButton('下一题(&X)')
        btnSubmit = QtWidgets.QPushButton('提交(&S)')
        self.btnSubmit = btnSubmit
        btn3 = QtWidgets.QPushButton('3分(&3)')
        btn2 = QtWidgets.QPushButton('2分(&2)')
        btn1 = QtWidgets.QPushButton('1分(&1)')
        btn0 = QtWidgets.QPushButton('0分(&0)')
        btnUnknown = QtWidgets.QPushButton('待定(&U)')

        btnCheck.clicked.connect(self.check_clicked)
        btnNext.clicked.connect(self.next_clicked)
        btnSubmit.clicked.connect(self.submit_clicked)
        btn3.clicked.connect(lambda:self.mark_btn_clicked(3))
        btn2.clicked.connect(lambda:self.mark_btn_clicked(2))
        btn1.clicked.connect(lambda:self.mark_btn_clicked(1))
        btn0.clicked.connect(lambda:self.mark_btn_clicked(0))
        btnUnknown.clicked.connect(lambda:self.mark_btn_clicked(-1))

        line = QtWidgets.QLineEdit()
        line.setText('3')
        self.markLine = line
        line.setMaximumWidth(80)

        hlayout.addWidget(btnNext)
        hlayout.addWidget(btnSubmit)
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

        hlayout.addWidget(QtWidgets.QLabel("当前题号"))

        numberEdit = QtWidgets.QLineEdit()
        self.numberEdit = numberEdit
        hlayout.addWidget(numberEdit)

        btnAdd = QtWidgets.QPushButton('+')
        btnAdd.clicked.connect(lambda:self.modify_number(1))
        btnAdd.setMaximumWidth(40)
        hlayout.addWidget(btnAdd)

        btnMinus = QtWidgets.QPushButton('-')
        btnMinus.clicked.connect(lambda:self.modify_number(-1))
        btnMinus.setMaximumWidth(40)
        hlayout.addWidget(btnMinus)

        # fileEdit = QtWidgets.QLineEdit()
        # self.fileEdit = fileEdit
        # hlayout.addWidget(QtWidgets.QLabel("当前文件名"))
        # hlayout.addWidget(fileEdit)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()

        btnTerminate = QtWidgets.QPushButton('中止(&A)')
        btnTerminate.clicked.connect(self.terminate_test)
        hlayout.addWidget(btnTerminate)

        btnLog = QtWidgets.QPushButton('本地记录(&L)')
        btnLog.clicked.connect(self.local_log)
        hlayout.addWidget(btnLog)

        note = QtWidgets.QLineEdit()
        self.noteLine = note
        label = QtWidgets.QLabel("批注(&N)")
        label.setBuddy(note)
        hlayout.addWidget(label)
        hlayout.addWidget(note)

        btnFast = QtWidgets.QPushButton('快速批注..(&F)')
        btnFast.clicked.connect(self.fast_note)
        hlayout.addWidget(btnFast)

        layout.addLayout(hlayout)

        for btn in (btnNext,btnTerminate,btnCheck,btn0,btn1,btn2,btn3,btnUnknown,btnLog,btnFast,btnSubmit):
            btn.setFixedHeight(50)
            btn.setMinimumWidth(120)
        for btn in (btnAdd,btnMinus):
            btn.setFixedHeight(50)

        for l in (line,numberEdit,note):
            l.setFixedHeight(40)
            font = QtGui.QFont()
            font.setPointSize(12)
            l.setFont(font)
        
        hlayout = QtWidgets.QHBoxLayout()
        outEdit = QtWidgets.QTextEdit()
        font = QtGui.QFont()
        font.setPointSize(11)
        outEdit.setFont(font)
        self.outEdit = outEdit
        QtWidgets.QScroller.grabGesture(self.outEdit,QtWidgets.QScroller.TouchGesture)
        hlayout.addWidget(outEdit)

        codeEdit = QtWidgets.QTextEdit()
        self.codeEdit = codeEdit
        QtWidgets.QScroller.grabGesture(self.codeEdit, QtWidgets.QScroller.TouchGesture)
        hlayout.addWidget(codeEdit)
        self.highLighter = HighLighter(codeEdit.document())


        layout.addLayout(hlayout)
        widget.setLayout(layout)

    def initToolBar(self):
        toolBar = QtWidgets.QToolBar(self)
        dirEdit = QtWidgets.QLineEdit()
        dirEdit.setText(self.workDir)

        self.dirEdit = dirEdit
        dirEdit.setMinimumWidth(800)
        label = QtWidgets.QLabel('工作路径(&C)')
        label.setBuddy(dirEdit)
        toolBar.addWidget(label)
        toolBar.addWidget(dirEdit)
        btnView = QtWidgets.QPushButton('浏览..(&V)')
        btnView.clicked.connect(self.view_dir)
        toolBar.addWidget(btnView)
        btnRefresh = QtWidgets.QPushButton("刷新工作区(&R)",self)
        btnRefresh.clicked.connect(self.refresh_workdir)
        self.btnRefresh = btnRefresh
        dirEdit.editingFinished.connect(btnRefresh.click)
        toolBar.addWidget(btnRefresh)

        btnNextDir = QtWidgets.QPushButton("下一文件夹(&D)")
        btnNextDir.clicked.connect(self.next_dir)
        self.btnNextDir = btnNextDir
        toolBar.addWidget(btnNextDir)

        self.addToolBar(toolBar)

        toolBar = QtWidgets.QToolBar(self)
        btnFile = QtWidgets.QPushButton('工作区文件夹')
        btnDir = QtWidgets.QPushButton('当前作业文件夹')
        btnExampleList = QtWidgets.QPushButton('测试用例表')
        btnExampleContent = QtWidgets.QPushButton('当前测试用例')

        toolBar.addWidget(btnFile)
        toolBar.addWidget(btnDir)
        toolBar.addWidget(btnExampleList)
        toolBar.addWidget(btnExampleContent)

        btnFile.clicked.connect(lambda:self.fileDock.setVisible(not self.fileDock.isVisible()))
        btnDir.clicked.connect(lambda :self.dirDock.setVisible(not self.dirDock.isVisible()))
        btnExampleList.clicked.connect(lambda:self.examplesDock.setVisible(not self.examplesDock.isVisible()))
        btnExampleContent.clicked.connect(lambda:self.currentExampleDock.setVisible(not self.currentExampleDock.isVisible()))

        btnAbout = QtWidgets.QPushButton('关于')
        btnAbout.clicked.connect(self.about)
        toolBar.addWidget(btnAbout)

        self.addToolBar(Qt.TopToolBarArea,toolBar)
    
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
        self.dirDock = dock

        listWidget = QtWidgets.QListWidget()
        dock.setWidget(listWidget)
        self.dirListWidget = listWidget
        listWidget.currentItemChanged.connect(self.dir_line_changed)

        self.addDockWidget(Qt.LeftDockWidgetArea,dock)

    def initExamplesDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle('测试用例表')
        self.examplesDock = dock

        listWidget = QtWidgets.QListWidget()
        listWidget.currentItemChanged.connect(self.example_changed)
        self.exampleList = listWidget
        dock.setWidget(listWidget)
        self.addDockWidget(Qt.RightDockWidgetArea,dock)

    def initCurrentExampleDock(self):
        dock = QtWidgets.QDockWidget()
        dock.setWindowTitle("本题目测试用例")
        self.currentExampleDock = dock

        textEdit = QtWidgets.QTextEdit()
        dock.setWidget(textEdit)
        self.exampleEdit = textEdit
        font = QtGui.QFont()
        font.setPointSize(11)
        textEdit.setFont(font)
        QtWidgets.QScroller.grabGesture(textEdit,QtWidgets.QScroller.TouchGesture)

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

    def getFastNotes(self):
        """
        从inputs/fastnotes.txt文件读取快速批注预案。
        """
        self.fastNotes.clear()
        try:
            fp = open('inputs/fastnotes.txt','r',encoding='utf-8',errors='ignore')
        except:
            return
        else:
            for line in fp:
                line = line.strip()
                if line:
                    self.fastNotes.append(line)

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
                    if '_MACOSX' not in a:
                        break
            if code_dir is not None and '_MACOSX' not in code_dir:
                break
        for t in os.scandir(code_dir):
            if not t.is_dir() and ('.c' in t.name or '.C' in t.name) and '.exe' not in t.name:
                filename = "{}\\{}".format(code_dir,t.name)
                self.dirListWidget.addItem(filename)
        if self.dirListWidget.count():
            self.dirListWidget.setCurrentRow(0)
        else:
            QtWidgets.QMessageBox.warning(self,'错误',"找不到源文件！")


    # slots
    def mark_btn_clicked(self,marks:int):
        if marks != -1:
            self.markLine.setText(str(marks))
        else:
            self.markLine.setText('待定')

    def check_clicked(self):
        if self.dirListWidget.currentItem() is None or self.exampleList.currentItem() is None:
            QtWidgets.QMessageBox.warning(self,'错误','测试当前题目：请先选择题目源文件和测试用例！')
            return
        self.checkAProblem(self.dirListWidget.currentItem().text(),
                           self.exampleList.currentItem().data(-1))

    def fast_note(self):
        """
        显示快速批注列表，选择要批注的条目返回。
        """
        if not self.fastNotes:
            QtWidgets.QMessageBox.information(self,'提示','没有快速批注文档。可将最可能用到的批注提前写好'
                                                        '放在inputs/fastnotes.txt文件内，一行一条。')
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('快速批注')
        dialog.resize(800,800)

        layout = QtWidgets.QVBoxLayout()
        listWidget = QtWidgets.QListWidget()

        listWidget.addItems(self.fastNotes)
        layout.addWidget(listWidget)

        btnOk = QtWidgets.QPushButton('确定')

        btnCancel = QtWidgets.QPushButton('取消')
        btnCancel.clicked.connect(dialog.close)
        btnOk.clicked.connect(lambda:self.fast_note_ok(listWidget,dialog))
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(btnOk)
        hlayout.addWidget(btnCancel)

        listWidget.itemDoubleClicked.connect(btnOk.click)
        listWidget.setCurrentRow(0)
        layout.addLayout(hlayout)

        dialog.setLayout(layout)
        dialog.exec_()

    def fast_note_ok(self,listWidget:QtWidgets.QListWidget,dialog:QtWidgets.QDialog):
        item = listWidget.currentItem()
        if item is None:
            return
        self.noteLine.setText(item.text())
        dialog.close()

    def submit_clicked(self):
        """
        提交
        """
        if self.fileListWidget.currentIndex() is None:
            self.statusBar().showMessage(f'{datetime.now().strftime("%H:%M:%S")} 当前选中为空，无法提交数据！')
            return
        status = ""
        number_str = self.numberEdit.text()
        try:
            number = int(number_str)
        except:
            number=-1
        if not 0<number<=self.dirListWidget.count():
            output = QtWidgets.QMessageBox.question(self,'问题','当前题号似乎不在题目范围内。是否继续提交？',
                                                    QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if output != QtWidgets.QMessageBox.Yes:
                self.statusBar().showMessage(f"{datetime.now().strftime('%H:%M:%S')} 放弃提交")
                return
        try:
            self.popenThread.terminate()
        except:
            pass
        with open(self.log_file,'a',encoding='utf-8',errors='ignore') as fp:
            # 文件夹全名，文件名, 批改时间, 题号，得分，批注
            cur_file_item = self.dirListWidget.currentItem()
            if cur_file_item is not None:
                cur_file = cur_file_item.text()
            else:
                cur_file = 'NA'
            note = f'{self.fileListWidget.currentItem().text()},' \
                   f'{cur_file},' \
                   f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")},' \
                   f'{number_str},'\
                     f'{self.markLine.text()},'\
                     f'{self.noteLine.text()}'
            fp.write(note+'\n')
            status += f"{datetime.now().strftime('%H:%M:%S')} 写入记录：{note}"
        self.statusBar().showMessage(status)
        self.noteLine.setText('')
        self.markLine.setText('3')

    def next_clicked(self):
        """
        下一题
        """
        # 先提交上一题的更改
        self.btnSubmit.click()
        status = self.statusBar().currentMessage()
        idx = self.dirListWidget.currentRow()
        # 2019.03.12调整：设置题号，再下一题。防止进入下一个时直接变成2.
        num = self.numberEdit.text()
        try:
            n = int(num)
        except:
            n = 0
        self.numberEdit.setText(str(n+1))
        if 0 <= idx < self.dirListWidget.count()-1:
            self.exampleList.setCurrentRow(self.exampleList.currentRow()+1)
            self.dirListWidget.setCurrentRow(self.dirListWidget.currentRow()+1)
        else:
            status += "||最后一个文件，自动进入下一个文件夹"
            self.btnNextDir.click()
        self.statusBar().showMessage(status)
        self.noteLine.setText('')
        self.markLine.setText('3')



    def view_dir(self):
        dir_ = QtWidgets.QFileDialog.getExistingDirectory(self,'选择工作区文件夹')
        if not dir_:
            return
        self.dirEdit.setText(dir_)
        self.btnRefresh.click()

    def refresh_workdir(self):
        """
        扫描当前工作区，初始化listWidget
        """
        if not self.dirEdit.text():
            return
        self.workDir = self.dirEdit.text()
        self.fileListWidget.clear()
        self.workDir.strip()
        self.workDir.rstrip('\\')
        self.workDir.rstrip('/')
        try:
            os.chdir(self.workDir)
            for t in os.scandir(self.workDir):
                if t.is_dir() and t.name not in ('__pycache__','inputs','backups'):
                    self.fileListWidget.addItem(t.name)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','文件夹非法\n'+repr(e))
            return
        self.log_file = self.workDir+'\\log.txt'
        with open(self.log_file,'a',encoding='utf-8',errors='ignore') as fp:
            fp.write(f'//打开时间：{datetime.now().strftime("%y-%m-%d %H:%M:%S")}\n')
        self.getExamples()
        self.getFastNotes()

    def checkAProblem(self,source:str,examples:list):
        """
        检查一道题，将结果输出到outEdit中。
        """
        note = pre_code(source)
        self.outEdit.setText(note)
        cmd_single = compile_cmd(source)
        cp_cmd = shell_cmd(cmd_single)

        p = QtCore.QProcess(self)
        p.start('cmd')
        p.waitForStarted()
        p.write(bytes(cp_cmd,'GBK'))
        p.waitForFinished(2000)
        out_str = read_out(p.readAllStandardOutput(),cmd_single)
        out_str += read_out(p.readAllStandardError(),cmd_single)

        self.outEdit.setHtml(self.outEdit.toHtml()+
                             '*************编译开始*************<br>'+out_str+
                             '<br>*************编译结束*************<br>')
        # 编译结束，更新窗口一次
        QtCore.QCoreApplication.processEvents()
        popenThread = PopenThread(source,self.workDir,examples)
        self.popenThread = popenThread
        popenThread.CheckFinished.connect(self.check_finished)
        popenThread.AllFinished.connect(self.check_all_finished)
        popenThread.start()

    # slots
    def check_finished(self,example,output_str):
        self.outEdit.setHtml(self.outEdit.toHtml()
        + f'<br><span style="color:#008000;">---------测试用例 {example}---------</span><br>' + output_str)

    def check_all_finished(self):
        self.outEdit.setHtml(self.outEdit.toHtml()
                             + '<br>===========测试正常结束===========<br>')

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
            try:
                self.exampleList.setCurrentRow(0)
            except:
                pass
            self.loadDir(item.text())
        self.numberEdit.setText("1")

    def dir_line_changed(self,item:QtWidgets.QListWidgetItem):
        """
        由dirListWidget切换触发。
        """
        if item is None:
            return
        idx = self.dirListWidget.currentRow()
        try:
            self.checkAProblem(item.text(),self.exampleList.currentItem().data(-1))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','自动测试失败，请手动点击测试\n'+repr(e))
        try:
            with open(item.text(),'r',encoding='GBK',errors='ignore') as fp:
                self.codeEdit.setText(fp.read())
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,'错误','文件错误\n'+repr(e))
        # self.fileEdit.setText(item.text())
        # self.numberEdit.setText(str(idx+1))
        # 2019.03.08：改为在next中调整。
    def example_changed(self,item:QtWidgets.QListWidgetItem):
        if item is None:
            return
        example_contents = []
        example_files = item.data(-1)
        for f in example_files:
            with open(self.workDir+'\\inputs\\'+f,errors='ignore') as fp:
                example_contents.append(f+'\n'+fp.read())
        self.exampleEdit.setText('\n\n====================\n'.join(example_contents))

    def terminate_test(self):
        print("terminate_test")
        if self.popenThread is not None:
            self.popenThread.terminate()
            self.outEdit.setHtml(self.outEdit.toHtml()+'<br>##########<br>测试中止<br>##########')
        print("terminate_test_ok")

    def local_log(self):
        """
        显示当前【文件夹】相关的本地记录。
        """
        if self.fileListWidget.currentItem() is None:
            QtWidgets.QMessageBox.warning(self,'错误','本地记录：请先选择文件夹')
            return
        curdir = self.fileListWidget.currentItem().text()

        dir_logs = []
        num_logs = []
        from log2excel import numFromDirName

        pro = QtWidgets.QProgressDialog(self)
        pro.setWindowTitle('正在读取')
        pro.setLabelText('正在读取文件')
        pro.setRange(0,0)
        with open(self.log_file,'r',encoding='utf-8',errors='ignore') as fp:
            for line in fp:
                # line尾巴上带了\n
                data = line.split(',',maxsplit=3)
                if len(data) != 4:
                    continue
                if data[0] == curdir:
                    dir_logs.append(line)
                elif numFromDirName(data[0]) == numFromDirName(curdir):
                    num_logs.append(line)
        pro.close()

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('本地记录')
        dialog.resize(800,800)
        layout = QtWidgets.QVBoxLayout()

        edit = QtWidgets.QTextEdit()
        edit.setFont(QtGui.QFont('sim sum',12))

        text = f"当前文件夹{curdir}的本地批改记录如下\n\n"

        text += "===============同名文件夹===============\n"
        text += "文件名，批改时间，题号，得分，批注\n"
        for d in dir_logs:
            text += f"{d.split(',',maxsplit=1)[1]}"
        text += f"\n\n===============其他可能是相同学号的文件夹===============\n"
        text += "文件夹，文件名，批改时间，题号，得分，批注\n"
        text += f"当前学号：{numFromDirName(curdir)}\n"
        for d in num_logs:
            text += f"{d}"

        edit.setText(text)
        layout.addWidget(edit)

        btnClose = QtWidgets.QPushButton('关闭')
        btnClose.clicked.connect(dialog.close)
        layout.addWidget(btnClose)

        dialog.setLayout(layout)

        dialog.exec_()

    def modify_number(self,t:int):
        """
        将当前题号调整1或-1.
        """
        n = self.numberEdit.text()
        try:
            num = int(n)
        except:
            num = 0
        self.numberEdit.setText(str(t+num))

    def about(self):
        text = self.name+'  '+self.version+'\n'
        text += self.date + '\n'
        text += '南京大学现代工程与应用科学学院  马兴越\n'
        text += 'https://github.com/CDK6182CHR/NJU_C_checker_multi'
        QtWidgets.QMessageBox.about(self,'关于',text)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        """
        关闭时将记录文件备份在代码目录下。
        """
        os.chdir(self.workDir)
        os.system("mkdir backups")
        back = '\\'
        os.system(f"copy log.txt backups{back}log_bak{datetime.now().strftime('%Y-%m-%d')}.txt")
        print("文件备份完毕")
        a0.accept()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = checkWindow()
    w.showMaximized()
    app.exec_()