"""
Author: HPC2H2
Date: 2025-03-21
Description: 
    定义CodeReadParser类，实现读取一工程目录，
    调用解析所有Py代码的类结构的效果。
"""
import os
import ast
from typing import List, Dict


class CodeReadParser: 
    def __init__(self, project_path: str):
        """
        代码解析器类，用于解析Python项目中的类定义、属性和方法。
        
        主要功能:
        - 递归遍历项目目录下的所有Python文件
        - 解析每个文件中的类定义
        - 提取类的属性、方法、父类等信息
        - 支持类型注解的解析
        - 支持多种文件编码
        
        使用方法:
        parser = CodeReadParser("项目路径")
        parser() # 执行解析
        parser.print_classes_info() # 打印解析结果
        
        类属性:
            project_path (str): 项目代码的绝对路径
            classes_path (Dict[str, str]): 类名与其所在文件路径的映射字典
            VALID_ENCODING (str): 有效的文件编码
            classes_info (Dict[str, Dict]): 存储解析后的类信息的字典,包含:
                - attributes: 类的属性及其类型
                - methods: 类的方法信息(方法名、参数、返回类型)
                - parent_classes: 父类列表
        """
        self.project_path = os.path.abspath(project_path)
        self.classes_path: Dict[str, str] = {}
        # 格式：
        # {
        #     "CodeReadParser": "code_read_parser.py",
        # }
        self.VALID_ENCODING: str = ""

        self.classes_info: Dict[str, Dict] = {}
        #  格式：
        # {
        #   "ClassName": {
        #       "attributes": {"name": type},
        #       "methods": [
        #           {"name": "method1", "args": ["arg1", "arg2"], "return_type": str},
        #       ],
        #       "parent_classes": ["BaseClass"]
        #   }
        # }

    def __call__(self):
        py_files = self._get_py_files() # 获取所有py文件
        self._get_encoding(py_files[0]) # 设置默认编码方式
        self._parse_all_files(py_files) # 解析所有py文件

    def _file_path_to_relative_path(self, file_path: str) -> str:
        """将文件路径转换为相对路径"""
        return os.path.relpath(file_path, self.project_path)
        
    def _get_py_files(self) -> List[str]:
        """读取所有py文件，返回包含它们完整路径的列表"""
        py_files = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".py"):
                    py_files.append(os.path.join(root, file))
        if len(py_files) == 0:
            raise IndexError("No python files found")
        return py_files
    
    def _get_encoding(self, file_path: str):
        """假设所有py代码文件编码都一样，读取一个存在self.VALID_ENCODING中"""
        # 打开并读取文件
        encodings = ["utf-8", "gbk", "latin-1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read()
                    self.VALID_ENCODING = enc
                    break
            except UnicodeDecodeError:
                print("Invalid encoding: ", enc)
                continue

    def _parse_all_files(self, py_files):
        """使用ast库解析每个python文件"""
        for file_path in py_files:
            with open(file_path, "r", encoding=self.VALID_ENCODING) as f:
                try:
                    tree = ast.parse(f.read())
                    self._register_classes(file_path, tree)
                except Exception as e:
                    print("Failed to parse file{file_path}: ", e)
    
    def _register_classes(self, file_path: str, tree: ast.Module):
        """注册类及其属性和方法"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                
                # 初始化类信息
                self.classes_info[class_name] = {
                    "attributes": {},
                    "methods": [],
                    "parent_classes": [base.id for base in node.bases if isinstance(base, ast.Name)]
                }
                
                # 存取类名和路径对应信息
                relative_path = self._file_path_to_relative_path(file_path)
                self.classes_path[class_name] = relative_path

                # 提取类内容
                self._extract_class_details(class_name, node)

    def _extract_class_details(self, class_name: str, class_node: ast.ClassDef):
        """提取类的详细内容"""
        for body_item in class_node.body:
            # 提取方法
            if isinstance(body_item, ast.FunctionDef):
                self._process_method(class_name, body_item)
            
            # 提取类属性（直接定义的属性）
            elif isinstance(body_item, ast.Assign):
                self._process_class_attribute(class_name, body_item)
            
            # 提取__init__中的实例属性（带有类型定义的属性）
            elif isinstance(body_item, ast.AnnAssign):
                self._process_annotated_attribute(class_name, body_item)

    def _process_method(self, class_name: str, method_node: ast.FunctionDef):
        """处理方法定义"""
        method_info = {
            "name": method_node.name,
            "args": self._extract_arguments(method_node.args),
            "decorators": [d.id for d in method_node.decorator_list if isinstance(d, ast.Name)],
            "return_type": self._extract_return_type(method_node)
        }
        
        # 特殊处理__init__方法
        if method_node.name == "__init__":
            self._process_init_method(class_name, method_node)
        else:
            self.classes_info[class_name]["methods"].append(method_info)

    def _extract_arguments(self, arguments: ast.arguments) -> List[str]:
        """提取方法参数"""
        args = []
        for arg in arguments.args:
            if arg.arg != 'self':  # 过滤self参数
                arg_type = (
                    ast.unparse(arg.annotation) 
                    if arg.annotation else "Any"
                )
                args.append(f"{arg.arg}: {arg_type}")
        return args

    def _extract_return_type(self, method_node: ast.FunctionDef) -> str:
        """提取返回类型"""
        if method_node.returns:
            return ast.unparse(method_node.returns)
        return "None"

    def _process_init_method(self, class_name: str, init_node: ast.FunctionDef):
        """处理__init__方法中的属性"""
        for stmt in init_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id == "self":
                            attr_name = target.attr
                            attr_type = ast.unparse(stmt.annotation) if hasattr(stmt, 'annotation') else "Any"
                            self.classes_info[class_name]["attributes"][attr_name] = attr_type

    def _process_class_attribute(self, class_name: str, assign_node: ast.Assign):
        """处理类级别属性（非实例属性）"""
        for target in assign_node.targets:
            if isinstance(target, ast.Name):
                attr_name = target.id
                attr_type = "Any"
                if isinstance(assign_node.value, ast.Constant):
                    attr_type = type(assign_node.value.value).__name__
                self.classes_info[class_name]["attributes"][attr_name] = attr_type

    def _process_annotated_attribute(self, class_name: str, ann_assign_node: ast.AnnAssign):
        """处理带类型注解的属性"""
        if isinstance(ann_assign_node.target, ast.Name):
            attr_name = ann_assign_node.target.id
            attr_type = ast.unparse(ann_assign_node.annotation)
            self.classes_info[class_name]["attributes"][attr_name] = attr_type

    def print_classes_info(self):
        """打印类信息，用等于号分隔"""
        for class_name, info in self.classes_info.items():
            print(f"Class: {class_name}")
            print(f"Attributes: {info['attributes']}")
            print("Methods:")
            for method in info['methods']:
                print(f"  {method['name']}({', '.join(method['args'])}) -> {method['return_type']}")
            print("\n" + "="*50)