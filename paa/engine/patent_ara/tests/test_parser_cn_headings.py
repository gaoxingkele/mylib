from __future__ import annotations

from patent_ara import PatentParser


def test_cn_parser_accepts_numbered_specification_headings():
    text = """发明名称：测试方法

一、技术领域
本发明涉及数据处理技术。

二、背景技术
现有系统存在处理延迟。

三、发明内容
本发明提供一种处理方法。

四、附图说明
图1是流程图。

五、具体实施方式
实施例一：获取数据并输出结果。

权利要求书
1. 一种测试方法，其特征在于，包括：获取数据；输出结果。
"""

    ara = PatentParser(lang="zh").parse(text)
    kinds = {section.kind for section in ara.spec_sections}

    assert {"field", "background", "summary", "drawings_brief", "embodiments", "claims"} <= kinds
