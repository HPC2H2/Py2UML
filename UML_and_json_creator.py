"""
Author: HPC2H2
Date: 2025-03-21
Description: 根据传入的类信息字典绘制UML图。
"""
import subprocess
import json
from typing import Dict,Optional

class JSONSaver:
    def __init__(self, classes_info: Dict[str, Dict] = None, \
                 json_path: str = "classes_info.json", encoding: str = "utf-8"):
        """
        JSON文件保存器类，用于将类信息保存为JSON格式文件。
        
        属性:
            classes_info (Dict[str, Dict]): 包含类信息的字典，格式为 {类名: {属性信息}}
            json_path (str): JSON文件保存路径，默认为 "classes_info.json"
            VALID_ENCODING (str): 文件编码格式，默认为 "utf-8"
        
        类信息字典格式要求:
            - 每个类必须包含 "attributes"、"methods" 和 "parent_classes" 三个键
            - attributes 必须为字典类型
            - methods 必须为字典列表
            - parent_classes 为父类信息
        
        示例:
            saver = JSONSaver(classes_info, "output.json")
            saver.save_to_json()
        """
        self.classes_info = classes_info
        self.json_path = json_path
        self.VALID_ENCODING = encoding

    def _validate_classes_info(self)->bool:
        "检查类信息是否有效"""
        if not self.classes_info:
            raise ValueError("classes_info is empty.")

        if not isinstance(self.classes_info, dict):
            raise TypeError("classes_info must be a dict.")
        
        for cls, info in self.classes_info.items():
            required_keys = {"attributes", "methods", "parent_classes"}
            # 验证必要字段
            if not required_keys.issubset(info.keys()):
                missing_keys = required_keys - info.keys()
                raise KeyError(f"{cls} missing keys: {missing_keys}")
            # 验证属性类型
            if not isinstance(info["attributes"], dict):
                raise TypeError(f"{cls} attributes must be a dict.")
            #验证方法类型
            if not all(isinstance(method, dict) for method in info["methods"]):
                raise TypeError(f"{cls} methods must be a list of dict.")
        return True
    
    def save_to_json(self):
        """将类信息保存为json文件"""
        if not self._validate_classes_info():
            raise ValueError("classes_info is not valid.")
        with open(self.json_path, "w", encoding=self.VALID_ENCODING) as f:
            json.dump(self.classes_info, f, indent=4)
        print(f"Saved to json file{self.json_path}.")

class UMLCreator(JSONSaver):
    def __init__(self, classes_info: Dict[str, Dict] = None, \
                json_path: Optional[str] = None, encoding: str = "utf-8", \
                uml_path: str = "UML_test.png"):
        """UML类图生成器
        
        该类继承自JSONSaver,用于将类信息转换为UML类图。支持从字典或JSON文件读取类信息,
        并使用Graphviz生成可视化的UML类图。
        
        属性:
            VALID_ENCODING (str): 文件编码格式
            uml_path (str): 生成的UML图片保存路径
            class_template (str): DOT文件的类节点模板
            classes_info (Dict): 存储类信息的字典
        
        参数:
            classes_info (Dict[str, Dict], optional): 类信息字典,包含属性、方法和父类信息
            json_path (str, optional): JSON文件路径,用于读取类信息
            encoding (str, default="utf-8"): 文件编码格式
            uml_path (str, default="UML_test.png"): UML图片保存路径
        
        异常:
            ValueError: 同时提供classes_info和json_path时抛出
            TypeError: classes_info格式错误时抛出
            KeyError: classes_info缺少必要键时抛出
            FileNotFoundError: JSON文件不存在时抛出
        """
        self.VALID_ENCODING = encoding
        self.uml_path = uml_path
        #创建 DOT 文件模板
        self.class_template = """
        {class_name} [
            shape=plaintext
            label=<
                <table border="0" cellborder="1" cellspacing="0">
                    <tr><td><b>{class_name}</b></td></tr>
                    {attributes}
                    {methods}
                </table>
            >
        ];
        """

        if classes_info and json_path:
            raise ValueError("Only to choose one data source, classes_info or json_path.")

        if json_path:
            self.classes_info = self.load_from_json(json_path)
        
        elif classes_info:
            self.classes_info = classes_info or {}
            self._validate_classes_info()
        # 此时 classes_info可能为空
    
    def load_from_json(self, json_path: str):
        """从json文件中读取类信息,返回格式化后的类信息字典"""
        try:
            with open(json_path, "r", encoding=self.VALID_ENCODING) as f:
                data = json.load(f)
                
                if not isinstance(data, dict):
                    raise TypeError("json file must be a dict.")
                return data
        except json.JSONDecodeError as e:
            raise ValueError("json file is not a valid json.") from e
        except FileNotFoundError as e:
            raise FileNotFoundError("json file not found.") from e
        
    def _validate_classes_info(self):
        """检查类信息是否有效"""
        if not isinstance(self.classes_info, dict):
            raise TypeError("classes_info must be a dict.")
        
        for cls, info in self.classes_info.items():
            required_keys = {"attributes", "methods", "parent_classes"}
            if not required_keys.issubset(info.keys()):
                missing_keys = required_keys - info.keys()
                raise KeyError(f"{cls} missing keys: {missing_keys}")
            
    def generate_dot(self) -> str:
        """将类信息转换为可供Graphviz渲染的DOT格式"""
        dot = ["digraph G {"]

        # 生成类节点
        for cls, info in self.classes_info.items():
            attrs = "\n".join(
                f'<tr><td align="left">- {name}: {type_}</td></tr>'
                for name, type_ in info["attributes"].items()
            )

            methods = "\n".join(
                f'<tr><td align="left">+ {m["name"]}(): {m["return_type"]}</td></tr>'
                for m in info["methods"]
            )

            dot.append(
                self.class_template.format(
                    class_name=cls,
                    attributes=attrs,
                    methods=methods
                )
            )

        # 添加继承关系
        for cls, info in self.classes_info.items():
            for parent in info["parent_classes"]:
                dot.append(f"{parent} -> {cls} [arrowhead=onormal];")

        dot.append("}")
        return "\n".join(dot)

    def render_dot(self,dot_code: str, output_file: str = "UML_Diagram.png"):
        """渲染DOT代码为图片"""
        with open("temp.dot", "w", encoding=self.VALID_ENCODING) as f:
            f.write(dot_code)

        subprocess.run(
            [
                "dot", "-Tpng", "temp.dot",
                "-o", output_file,
                "-Grankdir=BT"  # 设置布局方向为Bottom-Top
            ],
            check=True  # 添加check参数确保命令执行成功
        )
        print(f"Saved to {output_file}.")

    def create_uml(self):
        """生成UML图"""
        if not self.classes_info:
            raise ValueError("classes_info is empty.")
        dot_code = self.generate_dot()
        self.render_dot(dot_code, self.uml_path)