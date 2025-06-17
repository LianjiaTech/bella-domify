from typing import List, Optional, Literal, Any, Union
from pydantic import BaseModel, Field


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