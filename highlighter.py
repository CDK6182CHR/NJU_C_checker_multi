"""
参考文档重新改写的语法高亮模块. 参考：
---------------------
作者：basisworker
来源：CSDN
原文：https://blog.csdn.net/xiaoyangyang20/article/details/68923133
版权声明：本文为博主原创文章，转载请附上博文链接！
"""
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

class HighLighter(QSyntaxHighlighter):
    Rules = []
    Formats = {}
    def __init__(self,parent):
        super(HighLighter, self).__init__(parent)
        self.initializeFormats()
        KEYWORDS = ["auto", "break", "case", "char", "const", "continue", "default", "do",
                    "double", "else", "enum", "extern", "float", "for", "goto", "if", "int", "long",
                    "register", "short", "signed", "sizeof", "static", "return", "struct", "switch",
                    "typedef", "union", "unsigned", "void", "volatile", "while", ]
        BUILTINS = ["printf", "scanf"]
        CONSTANTS = ["false", "true", "NULL", "nullptr",
                     "EOF"]
        HighLighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
                                        "keyword"))
        HighLighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % builtin for builtin in BUILTINS])),
                                        "builtin"))
        HighLighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % constant
                      for constant in CONSTANTS])), "constant"))
        HighLighter.Rules.append((QRegExp(
            r"\b[+-]?[0-9]+[lL]?\b"
            r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
            r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                                        "number"))
        HighLighter.Rules.append((QRegExp(r"//.*"), "comment"))
        HighLighter.Rules.append((QRegExp(
            r"//.*?"
        ),
        "comment"))
        self.commentStartExp = QRegExp(r"/\*.*?\*/")
        self.commentEndExp = QRegExp(r"\*/")

    @staticmethod
    def initializeFormats():
        baseFormat = QTextCharFormat()
        baseFormat.setFontFamily("courier")
        baseFormat.setFontPointSize(12)
        for name, color in (("normal", Qt.black),
                            ("keyword", Qt.darkBlue), ("builtin", Qt.darkRed),
                            ("constant", Qt.darkGreen),
                            ("decorator", Qt.darkBlue), ("comment", Qt.darkGreen),
                            ("string", Qt.darkYellow), ("number", Qt.darkMagenta),
                            ("error", Qt.darkRed), ("pyqt", Qt.darkCyan),
                            ("prepro",Qt.darkCyan)):
            format = QTextCharFormat(baseFormat)
            format.setForeground(QColor(color))
            if name in ("keyword", "decorator"):
                format.setFontWeight(QFont.Bold)
            # if name == "comment":
            #     format.setFontItalic(True)
            HighLighter.Formats[name] = format

    def highlightBlock(self, text):
        NORMAL, TRIPLESINGLE, TRIPLEDOUBLE, ERROR = range(4)

        textLength = len(text)
        prevState = self.previousBlockState()

        self.setFormat(0, textLength,
                       HighLighter.Formats["normal"])

        if text.startswith("Traceback") or text.startswith("Error: "):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           HighLighter.Formats["error"])
            return
        if (prevState == ERROR and
            not (text.startswith(sys.ps1) or text.startswith("//"))):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           HighLighter.Formats["error"])
            return

        for regex, format in HighLighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length,
                               HighLighter.Formats[format])
                i = regex.indexIn(text, i + length)

        # Slow but good quality highlighting for comments. For more
        # speed, comment this out and add the following to __init__:
        # PythonHighlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        if not text:
            pass
        elif text[:2] == "//":
            self.setFormat(0, len(text),
                           HighLighter.Formats["comment"])
        elif text[0] == '#':
            self.setFormat(0,len(text),HighLighter.Formats["prepro"])
        else:
            stack = []
            for i, c in enumerate(text):
                if c in ('"', "'"):
                    if stack and stack[-1] == c:
                        stack.pop()
                    else:
                        stack.append(c)
                elif c == "//" and len(stack) == 0:
                    self.setFormat(i, len(text),
                                   HighLighter.Formats["comment"])
                    break
                elif c == "#" and len(stack) == 0:
                    self.setFormat(i, len(text),
                                   HighLighter.Formats["prepro"])
                    break

        self.setCurrentBlockState(NORMAL)

        # This is fooled by triple quotes inside single quoted strings
        for i, state in ((self.commentStartExp.indexIn(text),
                          TRIPLESINGLE),
                        ):
            if self.previousBlockState() == state:
                if i == -1:
                    i = text.length()
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 3,
                               HighLighter.Formats["string"])
            elif i > -1:
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(),
                               HighLighter.Formats["string"])