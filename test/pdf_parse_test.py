from pdf2docx import Converter, parse

test_dir = '../test_document/'
converter = Converter(test_dir+"外泌体.pdf")
tables = converter.extract_tables(start=0, end=2,
                                  extract_table_with_cell_pos=True,
                                  remove_watermark=True,
                                  debug=True,
                                  debug_file_name=test_dir+"页眉页脚测试-debug.pdf",
                                  sematic_parse=True,
                                  parse_stream_table=False)
print(tables)

# converter.convert(start=0, end=1, docx_filename=test_dir+"大连.docx")

