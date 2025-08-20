# document_parser

![python-version](https://img.shields.io/badge/python->=3.6-green.svg)
[中文](README.md) | [English Version](README_EN.md)

An open-source document parsing Python library by Beike. It can be used as a Python library or run as a service, supporting parsing and conversion of various document formats.

## Features

### Supported File Formats
- PDF
- Word documents (DOCX/DOC)
- Excel spreadsheets (XLSX/XLS)
- CSV files
- PowerPoint presentations (PPTX)
- Text files
- Image files

### Parsing Features
- **Layout Parse**: Extract basic document layout structure, including text blocks and image blocks
- **DomTree Parse**: Build detailed document object model for further processing and analysis
- **Markdown Conversion**: Convert parsing results to Markdown format

### Advanced Features
- **Image Processing**: Built-in large model OCR capability for extracting image information
- **Table Processing**: Parse table structures and content
- **Header/Footer Recognition**: Automatically identify and filter headers and footers
- **Multi-process Parsing**: Use parallel processing to improve parsing efficiency
- **Evaluation Annotation**: Built-in evaluation module for annotating PDF parsing details

![pdf_marked](./assets/pdf_marked.png)

## System Requirements
- Python >= 3.9
- Other dependencies (see requirements.txt)

When running as a service, it doesn't depend on Beike's OpenAI ecosystem, but the document parsing process depends on Beike's open-source File-API (File-API uploaded files are the data source for document-parser)

## Environment Configuration

The following environment variables need to be set:
- OPENAI_API_KEY: Key for calling OpenAI API
- OPENAI_BASE_URL: Base URL for OpenAI API
- OPENAPI_CONSOLE_KEY: Default global key for accessing OpenAI console interfaces to obtain metadata, mainly used to get the list of vision models. Users can implement their own `VisionModelProvider` to return a list of vision-supported models

## Quick Start

### Using as a Library

1. Install Dependencies
   ```shell
   pip install document_parser
   ```

2. Configuration
   ```python
   parser_config = ParserConfig(image_provider=ImageStorageProvider(),
                               ocr_model_name="gtp-4o",
                               # Whether to enable OCR capability
                               # If not enabled, vision_model_provider or vision_model_list doesn't need to be implemented or configured
                               ocr_enable=True,
                               vision_model_provider=OpenAIVisionModelProvider())
   parser_context.register_all_config(parser_config)
   parser_context.register_user("userId") # User ID for model requests, OCR usage will be affected if not set
   ```

3. Execute Parsing
   ```python
   converter = Converter(stream=stream) # Pass in as file stream
   dom_tree = converter.dom_tree_parse(
       remove_watermark=True,   # Whether to enable watermark removal
       parse_stream_table=False # Whether to parse streaming tables
   )
   ```

### Running as a Service

1. Download code from Git

2. Start Command
   ```bash
   uvicorn server.app:app --port 8080 --host 0.0.0.0
   ```

*Can also be packaged as a docker image according to your needs

## Advantages
The evaluation data in the following figure shows that Beike's self-developed parsing capability is strong, with higher accuracy (based on Beike's limited evaluation set):

![image2](./assets/evaluation.png)

## Acknowledgments

This project is based on secondary development of [pdf2docx](https://github.com/dothinking/pdf2docx). We would like to thank the original author and team for their outstanding contributions. pdf2docx extracts text, images, vectors and other raw data based on PyMuPDF, parses sections, paragraphs, tables, images, text and other layout and styles based on rules, etc. For specific functionality, please visit its GitHub address, providing important technical foundation for our document parsing functionality.

## More Articles

[PDF Parsing: A Journey from Vision to Structure](./assets/share.pdf)