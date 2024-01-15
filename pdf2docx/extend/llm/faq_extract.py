import asyncio
import logging
import time
from json import JSONDecodeError
from typing import Optional
from pydantic import BaseModel, parse_obj_as
import json
import openai
from openai import AsyncOpenAI

FAQ_EXTRACT_PROMPT = """
将下面的FAQ大块文本内容，切分为小块QA，按照JSON格式返回, 如果对应问题不存在答案，不返回QA对。
例如：
FAQ文本为:
Q：如何添加登录访问权限，A：请联系张子枫进行权限配置。
问题：测试环境登录不上去了，怎么办？答案：请检查是否连接了VPN。
如何打开百度地图？
返回JSON格式: 
[{{"Q":"如何添加登录访问权限","A":\"请联系张子枫进行权限配置"}},{{"Q":"测试环境登录不上去了，怎么办","A":"请检查是否连接了VPN"}}]
===========
FAQ文本：
{faq_text}
返回JSON格式:
"""


def _faq_extract(faq_text: str, *, model="gpt-3.5-turbo-1106"):
    faq_text = faq_text.replace('"', '\\"')
    prompt = FAQ_EXTRACT_PROMPT.format(faq_text=faq_text)
    response = openai.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.001,
        model=model)
    return response.choices[0].message.content


class FAQ(BaseModel):
    # 字段Q， 类型str，非必需
    Q: Optional[str] = None
    A: Optional[str] = None

    def __repr__(self):
        return f"FAQ(Q={self.Q}, A={self.A})"

    def __str__(self):
        return f"""
        Q:{self.Q}
        A:{self.A}
        """


def parse_faq(faq_json_str) -> Optional[list[FAQ]]:
    try:
        # faq_json_str = faq_json_str.replace("\\", "\\\\") # \\进行转义
        json_obj = json.loads(faq_json_str, strict=False)
        return [parse_obj_as(FAQ, json_dict) for json_dict in json_obj]
    except JSONDecodeError:
        logging.error(rf'json解析失败, json_str: {faq_json_str}')
        try:
            faq_json_str = faq_json_str.replace("\\", "\\\\")  # \\进行转义
            json_obj = json.loads(faq_json_str, strict=False)
            faqs = [parse_obj_as(FAQ, json_dict) for json_dict in json_obj]
            return [FAQ(Q=faq.Q.replace('\\\\', '\\'), A=faq.A.replace('\\\\', '\\')) for faq in faqs]
        except JSONDecodeError:
            return None


def faq_extract(faq_text: str) -> list[FAQ]:
    max_retrys = 5
    extract = None
    while max_retrys > 0 and extract is None:
        try:
            json_str = _faq_extract(faq_text)
        except openai.RateLimitError as ratelimit_error:
            logging.error(rf'faq_extract ratelimit error: {faq_text}, {ratelimit_error}')
            time.sleep(10)
            continue
        except Exception as exception:
            logging.error(rf'faq_extract error: {faq_text}, {exception}')
            break
        logging.info(rf'faq_extract: {json_str}')
        extract = parse_faq(json_str)
        max_retrys -= 1
    return extract


if __name__ == '__main__':
    faq_text = """
    奥丁常见问题-QA 格式
    Q1:如何配置奥丁报告的权限?
    具体请查看 wiki: https://wiki.lianjia.com/pages/viewpage.action?pageId=1127701668
    Q2:新建字段或 SQL 语句中，计算两个整数相除，得到的结果是整数，不是小数， 如 3/2,得到的是 1，而不是 1.5
    A2:在 presto 语法种，两个整数相除的结果还是整数，要想让结果变为小数，需要将 分子或分母中的一个用 cast 函数转换为 double，如:3/cast(2 as double)
    Q3:如何快速学习搭建奥丁报告?
    A3:具体请查看 wiki，《10 分钟学会创建奥丁看板》
    https://wiki.lianjia.com/pages/viewpage.action?pageId=1153943533
    报错类:
    Q4:行级权限不对，该怎么自查呢?常见行级权限问题有哪些?
    A4:一般是配置问题 1、简单自查方法:使用代客验权功能，看一下是不是配置问题，如用户实际的组织编 码和组织名称等，是否一致，是否在配置的行级权限模板里面;
    2、完整方法:奥丁 Wiki 里，有详细的有行级权限问题自查指南: https://wiki.lianjia.com/pages/viewpage.action?pageId=1127701798
    Q5:下载后的数据行数/条数不对应、或有串行问题(各个列对不齐)、文件为空，该 如何解决?或数据有 2W 条，下载后仅 202 条，该如何解决?
    A5:
    原因分析:文本字段中可能存在换行符
    解决方案: 1、找到可能存在换行符的字段(一般是用户手动输入的字段，比如评论)
    """

    PROMPT = """
    判断一下内容是否属于FAQ文档，如果是，输出:True，否则输出:False
    ==================
    {page_content}
    """
    text = """
    Q2:新建字段或 SQL 语句中，计算两个整数相除，得到的结果是整数，不是小数， 如 3/2,得到的是 1，而不是 1.5
    A2:在 presto 语法种，两个整数相除的结果还是整数，要想让结果变为小数，需要将 分子或分母中的一个用 cast 函数转换为 double，如:3/cast(2 as double)
    Q3:如何快速学习搭建奥丁报告?
    A3:具体请查看 wiki，《10 分钟学会创建奥丁看板》
    https://wiki.lianjia.com/pages/viewpage.action?pageId=1153943533
    报错类:
    Q4:行级权限不对，该怎么自查呢?常见行级权限问题有哪些?
    A4:一般是配置问题 1、简单自查方法:使用代客验权功能，看一下是不是配置问题，如用户实际的组织编 码和组织名称等，是否一致，是否在配置的行级权限模板里面;
    2、完整方法:奥丁 Wiki 里，有详细的有行级权限问题自查指南: https://wiki.lianjia.com/pages/viewpage.action?pageId=1127701798
    Q5:下载后的数据行数/条数不对应、或有串行问题(各个列对不齐)、文件为空，该 如何解决?或数据有 2W 条，下载后仅 202 条，该如何解决?
    A5:
    原因分析:文本字段中可能存在换行符
    解决方案: 1、找到可能存在换行符的字段(一般是用户手动输入的字段，比如评论) 
    """
    try:
        _faq_extract(text, model="gpt-4-0613")
    except openai.PermissionDeniedError as e:
        print('PermissionDeniedError')
    except Exception as e:
        print(e)
