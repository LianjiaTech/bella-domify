from typing import List, Optional, Literal, Any, Union
from pydantic import BaseModel, Field

from utils.tokens_util import count_tokens

layout_type_mapping = {
    "Catalog": "Catalog",
    "Title": "Title",
    "List": "ListItem",
    "Formula": "Formula",
    "Code": "Code",
    "Text": "Text",

    "Figure": "Figure",
    "FigureName": "FigureName",
    "FigureNote": "Text", # 目前实际解析出来没有

    "Table": "Table",
    "TableName": "TableName",
    "TableNote": "Text",  # 目前实际解析出来没有
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

        # 转换根节点，构建树结构（不计算path）
        standard_root = cls._from_domtree_nodes(domtree.get('root'), source_file)

        return cls(root=standard_root)

    @classmethod
    def _from_domtree_nodes(cls, node: dict, source_file: SourceFile) -> StandardNode:
        """
        处理所有节点
        """
        # 根节点，创建一个空的 StandardNode
        standard_root_node = StandardNode(
            source_file=source_file,
            summary="",
            tokens=0,  # 先设置为 0，后面再计算
            path=None,
            element=None,
            children=[]
        )

        # 递归处理子节点
        for child in node.get('child', []):
            standard_child = cls._from_domtree_node_to_base_info(child)  # 不传递path参数
            if standard_child:  # 确保子节点不为 None
                standard_root_node.children.append(standard_child)

        # 处理 FigureName 和 TableName 节点（合并节点）
        cls._process_special_nodes(standard_root_node)

        # 计算所有节点的path
        cls._calculate_paths(standard_root_node)

        # 计算 token 数量：子节点 token 数量之和
        tokens = 0
        for child in standard_root_node.children:
            tokens += child.tokens

        # 设置 token 数量
        standard_root_node.tokens = tokens

        return standard_root_node

    @classmethod
    def _calculate_paths(cls, node: StandardNode, parent_path: List[int] = None):
        """
        计算所有节点的path

        Args:
            node: 当前处理的节点
            parent_path: 父节点的path
        """
        if parent_path is None:
            parent_path = []

        # 为子节点计算path
        for i, child in enumerate(node.children, start=1):
            child_path = parent_path + [i]
            child.path = child_path

            # 如果是表格节点，还需要更新单元格的path
            if isinstance(child.element, StandardTableElement) and child.element.rows:
                for row in child.element.rows:
                    for cell in row.cells:
                        if cell.path and len(cell.path) > 0:
                            # 保留单元格自身的位置信息
                            cell_position = cell.path[0]
                            cell.path = child_path + [cell_position]

            # 递归计算子节点的path
            cls._calculate_paths(child, child_path)


    @classmethod
    def _process_special_nodes(cls, node: StandardNode):
        """
        处理特殊节点（FigureName 和 TableName）

        Args:
            node: 当前处理的节点
        """
        if not node or not node.children:
            return

        # 创建一个新的子节点列表，用于存储处理后的子节点
        new_children = []
        i = 0

        while i < len(node.children):
            current = node.children[i]

            # 检查当前节点是否为 FigureName 或 TableName
            if current.element and current.element.type in ['FigureName', 'TableName']:
                target_type = 'Figure' if current.element.type == 'FigureName' else 'Table'
                merged = False

                # 检查前一个节点
                if i > 0:
                    prev_sibling = node.children[i-1]
                    if prev_sibling.element and prev_sibling.element.type == target_type:
                        # 找到对应类型的前一个兄弟节点，合并节点
                        if cls._merge_nodes(prev_sibling, current, target_type):
                            merged = True

                # 如果没有与前一个节点合并，检查后一个节点
                if not merged and i < len(node.children) - 1:
                    next_sibling = node.children[i+1]
                    if next_sibling.element and next_sibling.element.type == target_type:
                        # 找到对应类型的后一个兄弟节点，合并节点
                        if cls._merge_nodes(next_sibling, current, target_type):
                            merged = True

                # 如果没有找到对应类型的兄弟节点，将当前节点类型改为 Text
                if not merged:
                    current.element.type = 'text'
                    new_children.append(current)
            else:
                new_children.append(current)

            i += 1

        # 更新子节点列表
        node.children = new_children

        # 递归处理子节点
        for child in node.children:
            cls._process_special_nodes(child)

    @classmethod
    def _merge_nodes(cls, target_node: StandardNode, source_node: StandardNode, node_type: str) -> bool:
        """
        合并两个节点，将source_node的信息合并到target_node中

        Args:
            target_node: 目标节点（Figure或Table节点）
            source_node: 源节点（FigureName或TableName节点）
            node_type: 节点类型（'Figure'或'Table'）

        Returns:
            bool: 是否成功合并
        """
        if node_type == 'Figure' and isinstance(target_node.element, StandardImageElement):
            # 将 FigureName 的文本作为 Figure 的 name
            target_node.element.name = source_node.element.text
            # 更新 tokens 计数
            target_node.tokens += source_node.tokens
            # 将 FigureName 的位置添加到 Figure 中
            target_node.element.positions += source_node.element.positions
            return True
        elif node_type == 'Table' and isinstance(target_node.element, StandardTableElement):
            # 将 TableName 的文本作为 Table 的 name
            target_node.element.name = source_node.element.text
            # 更新 tokens 计数
            target_node.tokens += source_node.tokens
            # 将 Table 的位置添加到 Figure 中
            target_node.element.positions += source_node.element.positions
            return True
        return False

    @classmethod
    def _from_domtree_node_to_base_info(cls, node: dict) -> Optional[StandardNode]:
        """
        将 单个Node 转换为 StandardNode，并未完成全部信息转换，path、tokens 等信息需要后续计算

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
        element_type = layout_type_mapping.get(element['layout_type'], "Text")  # 默认类型为 text
        print(f"Processing element type: {element['layout_type']}" )
        print(f"Processing element type: {element_type}" )
        print("===")
        positions = [StandardPosition(bbox=element['bbox'], page=element['page_num'][0])]  # 位置列表，目前page_num元素个数只会是1个

        standard_node = None
        if element_type == "Figure":
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
                path=[],  # 初始化为空列表，后续再计算
                element=StandardImageElement(
                    type=element_type,
                    positions=positions,
                    name="",
                    description="",
                    text=text,
                    image=image,
                ),
                children=[]
            )
        elif element_type == "Table":
            rows = []
            cell_texts = []  # 收集所有单元格的文本，用于计算 token 数量
            for row_data in element['rows']:
                cells = []
                if 'cells' in row_data:
                    for cell_data in row_data['cells']:
                        cell_text = cell_data.get('text', '')
                        cell_texts.append(cell_text)
                        # 不计算cell_path，后续再计算
                        cell = Cell(
                            path=[[cell_data['start_row'], cell_data['end_row'], cell_data['start_col'], cell_data['end_col']]],
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
                path=[],  # 初始化为空列表，后续再计算
                element=StandardTableElement(
                    type=element_type,
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
                path=[],  # 初始化为空列表，后续再计算
                element=StandardElement(
                    type=element_type,
                    positions=positions,
                    text=text
                ),
                children=[]
            )

        # 递归处理子节点
        if 'child' in node:
            for child in node['child']:
                standard_child = cls._from_domtree_node_to_base_info(child)
                if standard_child:  # 确保子节点不为 None
                    standard_node.children.append(standard_child)

        # 计算 token 数量：自身 text 的 token 数量 + 子节点 token 数量
        tokens = count_tokens(text)
        for child in standard_node.children:
            tokens += child.tokens

        # 设置 token 数量
        standard_node.tokens = tokens

        return standard_node


