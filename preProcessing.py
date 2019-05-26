"""
对源代码等的预处理，方便修改
"""
import chardet,re
from PyQt5.QtCore import QByteArray

def pre_code(src:str)->str:
    """
    预处理代码, 保存回文件。返回处理信息。
    """
    fp = open(src, 'rb')
    content_bin = fp.read()
    fp.close()
    note = ""
    try:
        content_bin.decode('gbk')
    except:
        for code in ("UTF-8","big5"):
            # code = chardet.detect(content_bin)["encoding"]
            print(f"编码转换: {code}->GBK")
            try:
                content_str = content_bin.decode(code).encode('gbk').decode('gbk')
            except:
                pass
            else:
                note = f"编码转换: {code}->GBK"
                with open(src, 'w') as fp:
                    fp.write(content_str)
                break
        else:
            note = "不能识别的源文件编码：非GBK, UTF-8, big5"


    with open(src,'r',encoding='GBK',errors='ignore') as fp:
        code = fp.read()
    code = replace_code(code)

    with open(src,'w',encoding='GBK',errors='ignore') as fp:
        fp.write(code)
    return note

def replace_code(source:str)->str:
    source = source.replace('_getch','getch')
    getch = re.findall('(getch *?\( *?\))',source)
    for g in getch:
        source = source.replace(g,'getchar(/*此语句由批改程序从getch替换*/)')
    return source

def compile_cmd(source:str)->str:
    """
    返回编译命令。
    """
    return f'gcc "{source}" -o "{source}.exe" --std=c99'

def run_cmd(source:str,example_file:str)->str:
    """
    返回执行程序命令。不包含尾部换行符。
    """
    return f'"{source}.exe" < "{example_file}" 2 123 45 5 6 17 8 9 '

def shell_cmd(cmd:str)->str:
    """
    将要执行的语句封装成实际要发送给程序的形式，并编译为字节码
    """
    cmds = f"""\
@echo off
echo ==================Python_C_checker_split_line=====================
{cmd}
echo ==================Python_C_checker_split_line=====================
    """
    return cmds

def read_out(output:QByteArray,cmd:str)->str:
    """
    cmd: 输入的命令内容。用其他颜色表示。
    """
    # 输出内容可能被截断，先处理尾巴
    for i in range(3):
        try:
            o = str(bytes(output),'GBK',errors='ignore')
        except UnicodeDecodeError as u:
            print(repr(u))
            output = output[:-1]
        else:
            break
    else:
        print("cannot decode output")
        return "Decode error"

    print("read out before split",o)
    osp = o.split('==================Python_C_checker_split_line=====================')
    if len(osp) < 3:
        print("意外的输出内容",o)
        s = o
    else:
        s = osp[2].strip().rstrip('echo')
    print("read out",s)
    s = s.replace('\n','<br>')
    s = s.replace(cmd,
                  f'<span style="color:#0000ff;">$&gt;&nbsp;{cmd.replace("<","&lt;")}</span><br>')
    return s