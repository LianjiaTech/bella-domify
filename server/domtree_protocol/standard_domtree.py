from typing import List, Optional, Literal, Any, Union
from pydantic import BaseModel, Field

from utils.tokens_util import count_tokens

block_type_mapping = {
    "Catalog": "text",
    "Title": "text",
    "List": "text",
    "Formula": "text",
    "Code": "text",
    "Text": "text",

    "Figure": "image",
    "FigureName": "text",
    "FigureNote": "text",

    "Table": "table",
    "TableName": "text",
    "TableNote": "text",
}

class SourceFile(BaseModel):
    id: str  # 文件ID，唯一标识符，类型为string
    name: str  # 文件名，文档的名称，类型为string
    type: Optional[str]  # 文件类型，例如：pdf、docx等
    mime_type: Optional[str]  # MIME类型，例如：application/pdf、application/msword等


class StandardPosition(BaseModel):
    bbox: List[float]  # 文档中的矩形坐标信息，例如：[90.1,263.8,101.8,274.3]
    page: int  # 页码


class StandardImage(BaseModel):
    type: Literal["image_url", "image_base64", "image_file"]  # 图片类型约束
    url: Optional[str] = None  # 链接地址
    base64: Optional[str] = None  # 图片base64编码
    file_id: Optional[str] = None  # 上传到file-api的文件ID


class Cell(BaseModel):
    """表格单元格"""
    path: Optional[List[Union[int, List[int]]]] = Field(default_factory=list)  # 单元格路径
    text: Optional[str] = None  # 文本内容


class StandardRow(BaseModel):
    """表格行"""
    cells: List[Cell] = Field(default_factory=list)  # 单元格列表


class StandardBaseElement(BaseModel):
    type: str  # 类型，例如["Text","Title","List","Catalog","Table","Figure","Formula","Code","ListItem"]
    positions: List[StandardPosition]  # 位置信息，可能跨页所以是个数组


class StandardElement(StandardBaseElement):
    text: Optional[str] = None  # 文本信息，图片ocr的文字


class StandardTableElement(StandardBaseElement):
    name: Optional[str] = None  # 如果类型是Table、Figure为其名字
    description: Optional[str] = None  # 如果类型是Table、Figure为其描述
    rows: List[StandardRow] = Field(default_factory=list)  # 表格行


class StandardImageElement(StandardElement):
    name: Optional[str] = None  # 如果类型是Table、Figure为其名字
    description: Optional[str] = None  # 如果类型是Table、Figure为其描述
    image: Optional[StandardImage] = None  # 图片信息


class StandardNode(BaseModel):
    source_file: Optional[SourceFile] = None  # 文档来源，表示文档的来源信息
    summary: Optional[str] = None  # 摘要，文档的简要概述
    tokens: Optional[int] = None  # token预估数量，文档中的token数量估计
    path: Optional[List[int]] = Field(default_factory=list)  # 编号的层级信息，例如：1.2.1
    element: Optional[Union[StandardElement, StandardImageElement, StandardTableElement]] = None  # 元素信息，当前节点的元素详情
    children: Optional[List["StandardNode"]] = Field(default_factory=list)  # 子节点信息，当前节点的所有子节点


class StandardDomTree(BaseModel):
    root: StandardNode  # 根节点

    @classmethod
    def from_domtree_dict(cls, domtree: dict, file_info):
        """
        将 DomTree 转换为 StandardDomTree

        Args:
            domtree: 源 DomTree 对象
            file_info: 文件信息字典，包含文件ID、文件名等信息
        Returns:
            StandardDomTree: 转换后的 StandardDomTree 对象
        """
        # 创建 SourceFile 对象
        source_file = None
        if file_info:
            source_file = SourceFile(
                id=file_info['id'],
                name=file_info['filename'],
                type=file_info.get('type'),
                mime_type=file_info.get('mime_type')
            )

        # 转换根节点
        standard_root = cls._from_standard_root_node(domtree.get('root'), source_file)

        return cls(root=standard_root)

    @classmethod
    def _from_standard_root_node(cls, node: dict, source_file: SourceFile) -> StandardNode:
        """
        处理根节点
        """
        # 如果是根节点，创建一个空的 StandardNode
        standard_node = StandardNode(
            source_file=source_file,
            summary="",
            tokens=0,  # 先设置为 0，后面再计算
            path=None,
            element=None,
            children=[]
        )

        # 递归处理子节点
        for child in node.get('child', []):
            standard_child = cls._from_standard_node(child)  # 移除 source_file 参数
            if standard_child:  # 确保子节点不为 None
                standard_node.children.append(standard_child)

        # 计算 token 数量：子节点 token 数量之和
        tokens = 0
        for child in standard_node.children:
            tokens += child.tokens

        # 设置 token 数量
        standard_node.tokens = tokens

        return standard_node


    @classmethod
    def _from_standard_node(cls, node: dict) -> Optional[StandardNode]:
        """
            将 Node 转换为 StandardNode

            Args:
                node: 源 Node 对象（字典格式）
            Returns:
                StandardNode: 转换后的 StandardNode 对象
            """
        if not node:
            return

        element = node['element']

        text = ""
        # 映射的类型
        element_type = block_type_mapping.get(element['layout_type'], "text")  # 默认类型为 text
        positions = []
        # 解析 order_num 为 path
        path = cls._parse_order_num(node['order_num'])

        standard_node = None
        if element_type == "image":
            # 处理图片信息
            image = None
            text = element.get('image_ocr_result', '')
            if 'image_link' in element and element['image_link']:
                image = StandardImage(
                    type="image_url",
                    url=element['image_link']
                )

            # 创建 StandardNode
            standard_node = StandardNode(
                summary="",
                tokens=0,  # 先设置为 0，后面再计算
                path=path,  # 设置解析后的 path
                element=StandardImageElement(
                    type=element['layout_type'],
                    positions=positions,
                    name="",
                    description="",
                    text=text,
                    image=image,
                ),
                children=[]
            )
        elif element_type == "table":
            rows = []
            cell_texts = []  # 收集所有单元格的文本，用于计算 token 数量
            for row_data in element['rows']:
                cells = []
                if 'cells' in row_data:
                    for cell_data in row_data['cells']:
                        cell_path = []
                        if 'order_num' in cell_data:
                            cell_path = cls._parse_order_num(cell_data['order_num'])

                        cell_text = cell_data.get('text', '')
                        cell_texts.append(cell_text)

                        cell = Cell(
                            path=cell_path,
                            text=cell_text
                        )
                        cells.append(cell)
                # 使用 StandardRow 的构造函数创建行
                row = StandardRow(cells=cells)
                rows.append(row)

            # 将所有单元格的文本合并，用于计算 token 数量
            text = " ".join(cell_texts)

            standard_node = StandardNode(
                summary="",
                tokens=0,  # 先设置为 0，后面再计算
                path=path,  # 设置解析后的 path
                element=StandardTableElement(
                    type=element['layout_type'],
                    positions=positions,
                    name="",
                    description="",
                    rows=rows
                ),
                children=[]
            )
        else:
            text = element.get('text', '')
            standard_node = StandardNode(
                summary="",
                tokens=0,  # 先设置为 0，后面再计算
                path=path,  # 设置解析后的 path
                element=StandardElement(
                    type=element['layout_type'],
                    positions=positions,
                    text=text
                ),
                children=[]
            )

        # 递归处理子节点
        if 'child' in node:
            for child in node['child']:
                standard_child = cls._from_standard_node(child)
                if standard_child:  # 确保子节点不为 None
                    standard_node.children.append(standard_child)

        # 计算 token 数量：自身 text 的 token 数量 + 子节点 token 数量
        tokens = count_tokens(text)
        for child in standard_node.children:
            tokens += child.tokens

        # 设置 token 数量
        standard_node.tokens = tokens

        return standard_node


    @staticmethod
    def _parse_order_num(order_num: str):
        """
        解析 order_num 字符串，转换为 path 列表

        Args:
            order_num: 格式如 "1.1.1.1" 或 "1.2.3.1-1-1-1"

        Returns:
            list: 解析后的 path 列表，如 [1, 1, 1, 1] 或 [1, 2, 3, [1, 1, 1, 1]]
        """
        if not order_num:
            return []

        # 检查是否包含连字符
        if '-' in order_num:
            # 处理形如 "1.2.3.1-1-1-1" 的情况
            parts = order_num.split('-')
            # 将主路径部分（点号分隔的部分）解析为整数列表
            main_parts = parts[0].split('.')
            main_path = [int(p) for p in main_parts[:-1] if p]  # 除了最后一个部分

            # 将最后一个主路径部分和所有子路径部分（连字符分隔的部分）合并为子列表
            sub_path = []
            if main_parts[-1]:  # 确保最后一个部分不为空
                sub_path.append(int(main_parts[-1]))
            for p in parts[1:]:
                if p:  # 确保部分不为空
                    sub_path.append(int(p))

            # 将子列表添加到主路径
            if main_path:
                main_path.append(sub_path)
                return main_path
            else:
                # 如果主路径为空，则直接返回子列表
                return sub_path
        else:
            # 处理形如 "1.1.1.1" 的情况
            return [int(p) for p in order_num.split('.') if p]