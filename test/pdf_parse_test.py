from pdf2docx import Converter, parse

test_dir = '../test_document/'
converter = Converter(test_dir+"办公.pdf")
# converter.convert(test_dir+"办公.docx", start=0, end=1)
tables = converter.extract_tables(start=1, end=2,
                                  extract_table_with_cell_pos=True,
                                  remove_watermark=True,
                                  debug=True,
                                  debug_file_name=test_dir+"办公-debug.pdf",
                                  sematic_parse=True,
                                  parse_stream_table=False)
# print(tables)

# converter.convert(start=0, end=1, docx_filename=test_dir+"大连.docx")

