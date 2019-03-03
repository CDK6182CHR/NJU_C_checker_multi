"""
对源代码等的预处理，方便修改
"""
import chardet

def pre_code(src:str)->str:
    """
    预处理代码, 保存回文件。返回处理信息。
    """
    fp = open(src, 'rb')
    content_bin = fp.read()
    note = ""
    try:
        content_bin.decode('gbk')
    except:
        code = chardet.detect(content_bin)["encoding"]
        print(f"编码转换: {code}->GBK")
        note = f"编码转换: {code}->GBK"
        content_str = content_bin.decode(code).encode('gbk').decode('gbk')
        fp.close()
        with open(src, 'w') as fp:
            fp.write(content_str)
    with open(src,'r',encoding='GBK',errors='ignore') as fp:
        code = fp.read()
        code = code.replace('getch()','getchar(/*此语句由批改程序从getch替换*/)')
    with open(src,'w',encoding='GBK',errors='ignore') as fp:
        fp.write(code)
    return note