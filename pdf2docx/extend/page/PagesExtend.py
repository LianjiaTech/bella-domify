from pdf2docx.page.Pages import Pages


class PagesExtend:
    def __init(self, pages: Pages):
        self.pages = pages

    def mark_page_header(self):
        """
        mark page header
        in page header, most text are common except for some numbers represent page number, chatpter number
        """
        header_blocks = self._possible_header_blocks()

        return None

    def _possible_header_blocks(self):
        # for each page, we collect the first blocks in each column in the first section
        page_header_blocks = []
        for page in self.pages:
            if not page.finalized:
                continue
            if not page.sections:
                continue
            page_header_blocks.append(
                [column.blocks[0] if column.blocks else None for column in page.sections[0]])
        return page_header_blocks

    def _possible_footer_blocks(self):
        # for each page, we collect the last blocks in each column in the last section
        page_footer_blocks = []
        for page in self.pages:
            if not page.finalized:
                continue
            if not page.sections:
                continue
            page_footer_blocks.append(
                [column.blocks[-1] if column.blocks else None for column in page.sections[-1]])
        return page_footer_blocks

    def mark_page_footer(self):
        """mark page footer"""
        return None
