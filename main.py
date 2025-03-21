"""
Author: HPC2H2
Date: 2025-03-21
Description: 
    程序运行的起点，
    完成从读取工程目录到保存类信息到JSON文件中、输出UML类图的操作
"""

from code_read_parser import CodeReadParser
from UML_and_json_creator import JSONSaver, UMLCreator
def main():
    cparser = CodeReadParser("E:\\BaiduSyncdisk\\Py2UML") # 实例化
    cparser() # 解析
    cparser.print_classes_info() # 打印信息
    # 保存到json文件中
    JSONSaver(classes_info=cparser.classes_info, json_path="classes_info.json", \
                         encoding=cparser.VALID_ENCODING).save_to_json()
    # 根据json文件生成UML图
    UMLCreator(json_path="classes_info.json", uml_path="UML_Diagram1.png", \
                             encoding=cparser.VALID_ENCODING).create_uml()
    # 根据类信息字典生成UML图
    UMLCreator(classes_info=cparser.classes_info, uml_path="UML_Diagram2.png", \
                             encoding=cparser.VALID_ENCODING).create_uml()

if __name__ == "__main__":
    main()
