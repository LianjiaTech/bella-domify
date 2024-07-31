# -*- coding: utf-8 -*-
# ===============================================================
#
#    Copyright (C) 2024 Beike, Inc. All Rights Reserved.
#
#    @Create Author : luxu(luxu002@ke.com)
#    @Create Time   : 2024/7/30
#    @Description   : 
#
# ===============================================================

DEFAULT_SETTINGS = {
    'debug': False,  # plot layout if True
    'ocr': 0,  # ocr status: 0 - no ocr; 1 - to do ocr; 2 - ocr-ed pdf
    'ignore_page_error': True,  # not break the conversion process due to failure of a certain page if True
    'multi_processing': False,  # convert pages with multi-processing if True
    'cpu_count': 0,  # working cpu count when convert pages with multi-processing
    'min_section_height': 20.0,  # The minimum height of a valid section.
    'connected_border_tolerance': 0.5,  # two borders are intersected if the gap lower than this value
    'max_border_width': 6.0,  # max border width
    'min_border_clearance': 2.0,  # the minimum allowable clearance of two borders
    'float_image_ignorable_gap': 5.0,  # float image if the intersection exceeds this value
    'page_margin_factor_top': 0.5,  # [0,1] reduce top margin by factor
    'page_margin_factor_bottom': 0.5,  # [0,1] reduce bottom margin by factor
    'shape_min_dimension': 2.0,  # ignore shape if both width and height is lower than this value
    'max_line_spacing_ratio': 1.5,  # maximum line spacing ratio: line spacing / line height
    'line_overlap_threshold': 0.9,  # [0,1] delete line if the intersection to other lines exceeds this value
    'line_break_width_ratio': 0.5,
    # break line if the ratio of line width to entire layout bbox is lower than this value
    'line_break_free_space_ratio': 0.1,
    # break line if the ratio of free space to entire line exceeds this value
    'line_separate_threshold': 5.0,  # two separate lines if the x-distance exceeds this value
    'new_paragraph_free_space_ratio': 0.85,
    # new paragraph if the ratio of free space to line height exceeds this value
    'lines_left_aligned_threshold': 1.0,  # left aligned if d_x0 of two lines is lower than this value (Pt)
    'lines_right_aligned_threshold': 1.0,  # right aligned if d_x1 of two lines is lower than this value (Pt)
    'lines_center_aligned_threshold': 2.0,
    # center aligned if delta center of two lines is lower than this value
    'clip_image_res_ratio': 4.0,  # resolution ratio (to 72dpi) when clipping page image
    'min_svg_gap_dx': 15.0,  # merge adjacent vector graphics if the horizontal gap is less than this value
    'min_svg_gap_dy': 2.0,  # merge adjacent vector graphics if the vertical gap is less than this value
    'min_svg_w': 2.0,  # ignore vector graphics if the bbox width is less than this value
    'min_svg_h': 2.0,  # ignore vector graphics if the bbox height is less than this value
    'extract_stream_table': False,  # don't consider stream table when extracting tables
    'parse_lattice_table': True,  # whether parse lattice table or not; may destroy the layout if set False
    'parse_stream_table': True,  # whether parse stream table or not; may destroy the layout if set False
    'delete_end_line_hyphen': False,  # delete hyphen at the end of a line
    'remove_watermark': False,  # remove watermark if True
}
