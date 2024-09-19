#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup

DESCRIPTION = 'Open source Python library converting pdf to docx.'
EXCLUDE_FROM_PACKAGES = ["build", "dist", "test"]


# read version number from version.txt, otherwise alpha version
# Github CI can create version.txt dynamically.
def get_version(fname):
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            version = f.readline().strip()
    else:
        version = '0.1.3.10'

        """
        发包命令：
        python setup.py bdist_wheel upload -r ke

        版本说明：
        version = '0.1.1.0‘  20240816   页眉新方案上线；
        version = '0.1.2.0‘  20240822   目录、封面识别并去除；接口解析接口图片附带S3链接；
        version = '0.1.3.0‘  20240823   封面识别前提大于3页(含)
        version = '0.1.3.1‘  20240826   parser日志输出优化
        version = '0.1.3.2‘  20240826   读取config强校验去除
        version = '0.1.3.4‘  20240829   修复特殊字符引起的解析结果打印异常;页脚阈值放宽;
        version = '0.1.3.6‘  20240830   不常见字体兼容；
        version = '0.1.3.7‘  20240912   FAQ文件QA切分输出；
        version = '0.1.3.10‘  20240919   大文件oom问题优化；
        
        """

    return version


# Load README.md for long description
def load_long_description(fname):
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            long_description = f.read()
    else:
        long_description = DESCRIPTION

    return long_description


def load_requirements(fname):
    try:
        # pip >= 10.0
        from pip._internal.req import parse_requirements        
    except ImportError:
        # pip < 10.0
        from pip.req import parse_requirements

    reqs = parse_requirements(fname, session=False)
    try:
        requirements = [str(ir.requirement) for ir in reqs]
    except AttributeError:
        requirements = [str(ir.req) for ir in reqs]

    return requirements

setup(
    name="document_parser",
    version=get_version("version.txt"),
    keywords=["document-parser"],
    description=DESCRIPTION,
    long_description=load_long_description("README.md"),
    long_description_content_type="text/markdown",
    license="GPL v3",
    author=["tangxiaolong", "luxu", "zhangxiaojia"],
    author_email=["tangxiaolong@ke.com", "luxu002@ke.com", "zhangxiaojia002@ke.com"],
    url="https://git.lianjia.com/ai-arch/document_parse",
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    include_package_data=True,
    zip_safe=False,
    install_requires=load_requirements("requirements.txt"),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "pdf2docx=pdf2docx.main:main"
        ]
    },
)
