from pdf2docx import Converter, parse

test_dir = '../test_document/'
converter = Converter(test_dir + "大连.pdf")
dom_tree = converter.dom_tree_parse(
    # start=0, end=1,
    remove_watermark=True,
    debug=True,
    debug_file_name=test_dir + "大连-debug.pdf",
    parse_stream_table=False
)
