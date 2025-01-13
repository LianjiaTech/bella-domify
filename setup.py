#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup

DESCRIPTION = 'Open source Python library converting pdf to docx.'
EXCLUDE_FROM_PACKAGES = ["build", "dist", "test"]

VERSION = "0.1.6.3"


# 获取主版本号
# 输入0.1.5.5 输出0.1.5
def get_main_version(version):
    return version.rsplit('.', 1)[0]


# read version number from version.txt, otherwise alpha version
# Github CI can create version.txt dynamically.
def get_version(fname):
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            version = f.readline().strip()
    else:
        version = VERSION

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


if __name__ == "__main__":
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

"""
发包命令：

    python setup.py bdist_wheel upload -r ke

版本说明：

    version = '0.1.1.0'  20240816   页眉新方案上线；
    
    version = '0.1.2.0'  20240822   目录、封面识别并去除；接口解析接口图片附带S3链接；
    
    version = '0.1.3.0'  20240823   封面识别前提大于3页(含)
    version = '0.1.3.1'  20240826   parser日志输出优化
    version = '0.1.3.2'  20240826   读取config强校验去除
    version = '0.1.3.4'  20240829   修复特殊字符引起的解析结果打印异常;页脚阈值放宽;
    version = '0.1.3.6'  20240830   不常见字体兼容；
    version = '0.1.3.7'  20240912   FAQ文件QA切分输出；
    version = '0.1.3.10'  20240919   大文件oom问题优化；
    version = '0.1.3.11'  20240919   image_s3_link属性丢失问题修复；
    version = '0.1.3.12'  20240920   特殊字体的默认读入设置改为Helvetica；
    version = '0.1.3.13'  20240923   block切分准确率：0.96；
    
    version = '0.1.4.0'  20240923   block优化里程碑（同0.1.3.13）；
    
    version = '0.1.5.0'  20241022   层级优化里程碑0.80  (336 / 422)；
    version = '0.1.5.1'  20241023   bug修复；
    version = '0.1.5.2'  20241023   bug修复；
    version = '0.1.5.4'  20241024   目录过滤，默认值改为是；
    version = '0.1.5.5'  20241104   页眉阈值优化；
    version = '0.1.6.0'  20241126   block优化（跨列合并、单行文字字号不统一等）横版pdf忽略页眉识别；
    version = '0.1.6.1'  20241206   bug修复，获取字体等统计量时兼容image；
    version = '0.1.6.2'  20241209   依赖版本修改openpyxl==3.1.5；
    version = '0.1.6.3'  20250113   优化FAQ判断逻辑（添加空页情况兼容）；

"""