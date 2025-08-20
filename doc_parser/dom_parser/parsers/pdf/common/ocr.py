import time

import openai
import requests

from doc_parser.context import parser_context, logger_context

logger = logger_context.get_logger()


def llm_image2text(image_url, user, model=parser_context.ocr_model_name):
    if not parser_context.ocr_enable:
        logger.info("OCR功能未开启")
        return ""
    if not model:
        logger.error("无法提供ocr内容，原因：model未指定")
        return ""
    if not user:
        logger.error("无法提供ocr内容，原因：user未提供")
        return ""
    if not image_url:
        return ""
    if not is_vision_model(model):
        logger.error(f"无法提供ocr内容，原因：模型{model}不支持视觉输入")
        return ""

    PROMPT = """
    请从图片中提取出表达的信息，注意，只提取文字和结构，禁止修改文字，禁止二次加工，不做描述，以免曲解原意

    如果图片中有表格，表格部分可以以markdown方式来表达；对于合并单元格的情况，可以用相同的冗余列来表示，保证表格的行数列数一致；
    如果图片中有流程图，流程图部分可以用mermaid方式表达；
    如果图片中有柱状图、饼图、折线图等这样文字占比很小，无法用文字准确表达含义的部分，直接从枚举值【柱状图、饼图、折线图】等选择一个输出图表类型；
    如果只是段落，直接提取出原文即可；
    如果没有文字，则直接返回‘无文字’；
    """

    max_retry = 3
    response = None
    while max_retry > 0 and response is None:
        max_retry -= 1
        try:
            logger.info(f"图片信息提取请求LLM中【模型名：{model}】")
            response = openai.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                },
                            },
                        ],
                    }
                ],
                temperature=0.001,
                top_p=0.01,
                model=model,
                user=user,
                timeout=30  # 超时时间为30秒
            )
            logger.info(f"图片信息提取请求LLM中，【请求结果：{response}】")
        except openai.RateLimitError:
            time.sleep(10)
        except requests.exceptions.Timeout:
            logger.error("请求超时")
            break
        except Exception as e:
            logger.error("openai chat error: %s", e)
            break
    if response is None or not response.choices:
        logger.error("图片信息提取请求失败")
        return "[图片OCR失败]"
    ocr_text = response.choices[0].message.content
    if not ocr_text or ocr_text == "无":
        ocr_result = f"[图片OCR内容为空]"
        return ocr_result
    else:
        ocr_text = str(ocr_text)
        ocr_result = \
            f"[图片OCR内容]\n{ocr_text}"
        return ocr_result


def is_vision_model(model: str) -> bool:
    """
    检查模型是否为视觉模型

    参数:
        model: 模型名称(str)

    返回:
        是否为视觉模型(bool)
    """
    if parser_context.vision_model_provider:
        return model in parser_context.vision_model_provider.get_model_list()

    if parser_context.vision_model_list:
        return model in parser_context.vision_model_list

    raise ValueError("vision_model_list_provider or vision_model_list is not set in parser_context")

