import logging

from pdf2docx import Converter, parse

# logging_level = logging.INFO
# main_logger = logging.getLogger()
# main_logger.setLevel(logging_level)
#
# # Set up a stream handler to log to the console
# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging_level)
# formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# stream_handler.setFormatter(formatter)
#
# # Add handler to logger
# main_logger.addHandler(stream_handler)

test_dir = '../test_document/'
converter = Converter(test_dir + "奥丁QA.pdf")
dom_tree = converter.dom_tree_parse(
    start=0, end=2,
    remove_watermark=True,
    debug=True,
    debug_file_name=test_dir + "奥丁QA-debug.pdf",
    parse_stream_table=False
)
