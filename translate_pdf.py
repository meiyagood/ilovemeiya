#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 翻译工具 — 英文 → 中文
生成：① 中英双语版 PDF  ② 纯中文版 PDF
翻译结果自动缓存到 .json，下次重复运行不重复调用翻译 API。

用法:
    python3 translate_pdf.py <input.pdf>
    python3 translate_pdf.py          # 自动查找当前目录下唯一的 PDF
"""

import os
import sys
import time
import math
import json
from xml.sax.saxutils import escape as xml_escape

import pdfplumber
from deep_translator import GoogleTranslator
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ═══════════════════════════════════════════════════════
#  1. 字体注册
# ═══════════════════════════════════════════════════════

def setup_fonts() -> str:
    """注册中文字体，返回字体名；若系统字体均不可用则用内置 CID 字体。"""
    candidates = [
        ("/System/Library/Fonts/PingFang.ttc",           "PingFang"),
        ("/System/Library/Fonts/STHeiti Light.ttc",      "STHeiti"),
        ("/System/Library/Fonts/Supplemental/Songti.ttc","Songti"),
        ("/Library/Fonts/Arial Unicode MS.ttf",          "ArialUnicode"),
    ]
    for path, name in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                print(f"✓ 字体加载成功: {os.path.basename(path)}")
                return name
            except Exception as e:
                print(f"  字体加载失败 {path}: {e}")

    # 回退：reportlab 内置 CID 字体（需 rlPyCairo / CJK 扩展）
    try:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        print("✓ 使用内置 STSong-Light 字体")
        return "STSong-Light"
    except Exception as e:
        print(f"  内置 CID 字体失败: {e}")

    print("⚠ 未找到中文字体，中文可能显示为方框")
    return "Helvetica"


# ═══════════════════════════════════════════════════════
#  2. 翻译工具
# ═══════════════════════════════════════════════════════

def translate_text(text: str, translator: GoogleTranslator, retries: int = 3) -> str:
    """翻译文本；自动分块处理超过 4000 字符的长文本。"""
    if not text or not text.strip():
        return text or ""

    MAX = 4000
    if len(text) <= MAX:
        for attempt in range(retries):
            try:
                time.sleep(0.45)   # 限速，避免 429
                result = translator.translate(text)
                return result or text
            except Exception as e:
                wait = 2 ** attempt
                print(f"  ⚠ 翻译重试 ({attempt+1}/{retries})，等待 {wait}s：{e}")
                time.sleep(wait)
        print("  ✗ 翻译失败，保留原文")
        return text

    # 超长文本：按段落分块
    lines = text.split("\n")
    chunks, cur, cur_len = [], [], 0
    for line in lines:
        if cur_len + len(line) + 1 > MAX and cur:
            chunks.append("\n".join(cur))
            cur, cur_len = [], 0
        cur.append(line)
        cur_len += len(line) + 1
    if cur:
        chunks.append("\n".join(cur))

    return "\n".join(translate_text(c, translator, retries) for c in chunks)


def translate_table(rows: list, translator: GoogleTranslator) -> list:
    """翻译表格；返回每格 {'original': ..., 'translated': ...} 字典。"""
    total = sum(1 for row in rows for cell in row if cell and str(cell).strip())
    done = 0
    result = []
    for row in rows:
        new_row = []
        for cell in row:
            orig = str(cell).strip() if cell is not None else ""
            if orig:
                trans = translate_text(orig, translator)
                done += 1
                if done % 10 == 0:
                    print(f"  已翻译单元格: {done}/{total}")
            else:
                trans = ""
            new_row.append({"original": orig, "translated": trans})
        result.append(new_row)
    return result


# ═══════════════════════════════════════════════════════
#  3. PDF 内容提取
# ═══════════════════════════════════════════════════════

def extract_pdf(pdf_path: str) -> list:
    """
    逐页提取内容。
    优先提取表格；若该页无表格则提取文本。
    返回 list of {'type': 'table'|'text', 'data': ...}
    """
    items = []
    settings = {
        "vertical_strategy":   "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance":      3,
    }
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            print(f"  提取第 {i+1}/{total} 页…")
            tables = page.extract_tables(table_settings=settings)

            if tables:
                for tbl in tables:
                    clean = [row for row in tbl
                             if any(c and str(c).strip() for c in row)]
                    if clean:
                        items.append({"type": "table", "data": clean})
            else:
                text = page.extract_text()
                if text and text.strip():
                    items.append({"type": "text", "data": text})
    return items


# ═══════════════════════════════════════════════════════
#  4. 翻译所有内容
# ═══════════════════════════════════════════════════════

def translate_all(content: list) -> list:
    """对提取的内容逐块翻译，返回翻译后的结构。"""
    translator = GoogleTranslator(source="en", target="zh-CN")
    translated = []
    n = len(content)

    for idx, item in enumerate(content):
        print(f"\n  翻译内容块 {idx+1}/{n}（类型: {item['type']}）…")
        if item["type"] == "table":
            trans_data = translate_table(item["data"], translator)
            translated.append({"type": "table", "data": trans_data})
        else:
            trans_text = translate_text(item["data"], translator)
            translated.append({
                "type": "text",
                "original":   item["data"],
                "translated": trans_text,
            })
    return translated


# ═══════════════════════════════════════════════════════
#  5. PDF 构建工具
# ═══════════════════════════════════════════════════════

def make_styles(font: str) -> dict:
    return {
        "h1": ParagraphStyle(
            "h1", fontName=font, fontSize=14, leading=20,
            spaceBefore=10, spaceAfter=8, alignment=TA_CENTER,
            textColor=colors.HexColor("#1a3a5c"),
        ),
        "h2": ParagraphStyle(
            "h2", fontName=font, fontSize=10, leading=15,
            spaceBefore=8, spaceAfter=4,
            textColor=colors.HexColor("#2c5f8a"),
        ),
        "body_cn": ParagraphStyle(
            "body_cn", fontName=font, fontSize=9, leading=14,
            spaceBefore=2, spaceAfter=2,
        ),
        "body_en": ParagraphStyle(
            "body_en", fontName="Helvetica", fontSize=7.5, leading=11,
            spaceBefore=1, spaceAfter=2,
            textColor=colors.HexColor("#777777"),
        ),
        "cell_cn": ParagraphStyle(
            "cell_cn", fontName=font, fontSize=8, leading=12,
        ),
        "cell_en": ParagraphStyle(
            "cell_en", fontName="Helvetica", fontSize=6.5, leading=10,
            textColor=colors.HexColor("#999999"),
        ),
    }


def s(text: str) -> str:
    """对 XML/HTML 特殊字符转义，防止 Paragraph 报错。"""
    return xml_escape(str(text or ""))


# 可用页面高度（A4 减去上下边距）
_PAGE_H = A4[1] - 3.5 * cm


def _cell_font_size(cn_len: int, en_len: int, col_w: float) -> tuple:
    """根据单元格内容长度和列宽自动计算合适字号，防止单元格超出页面高度。"""
    for cn_sz in (8.0, 7.0, 6.0, 5.5, 5.0, 4.5, 4.0, 3.5):
        en_sz = max(3.0, cn_sz - 1.5)
        leading = cn_sz * 1.5
        # 中文字宽约 font_size*0.9，英文约 font_size*0.6
        avg_w = (cn_sz * 0.9 * cn_len + en_sz * 0.6 * en_len) / max(1, cn_len + en_len)
        chars_line = col_w / max(1, avg_w)
        total_lines = (cn_len + en_len) / max(1, chars_line)
        est_h = total_lines * leading + 10  # 10pt 内边距
        if est_h < _PAGE_H:
            return cn_sz, en_sz
    return 3.5, 3.0


def _split_text_chunks(text: str, max_chars: int) -> list:
    """在换行符处将长文本切分为若干段，每段不超过 max_chars 字符。"""
    if len(text) <= max_chars:
        return [text]
    # 先按换行符切分；对超长单行按字符强制切断
    raw_lines = text.split("\n")
    lines = []
    for ln in raw_lines:
        while len(ln) > max_chars:
            lines.append(ln[:max_chars])
            ln = ln[max_chars:]
        lines.append(ln)
    chunks, cur, cur_len = [], [], 0
    for line in lines:
        if cur_len + len(line) + 1 > max_chars and cur:
            chunks.append("\n".join(cur))
            cur, cur_len = [], 0
        cur.append(line)
        cur_len += len(line) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks or [text]


def _expand_rows(trans_rows: list, max_cell_chars: int = 700) -> list:
    """
    把含有超长单元格的行拆分为多行，以防止单行高度超过页面。
    拆分时按换行符自然断开，其余列保持空白。
    """
    result = []
    for row in trans_rows:
        # 找到最长的单元格
        max_len = max(len(c["translated"]) + len(c["original"]) for c in row)
        if max_len < max_cell_chars:
            result.append(row)
            continue

        # 找出哪个单元格最长，按该列拆分行
        pivot = max(range(len(row)),
                    key=lambda i: len(row[i]["translated"]) + len(row[i]["original"]))

        cn_chunks = _split_text_chunks(row[pivot]["translated"], max_cell_chars // 2)
        en_chunks = _split_text_chunks(row[pivot]["original"],  max_cell_chars // 2)
        n = max(len(cn_chunks), len(en_chunks))
        cn_chunks += [""] * (n - len(cn_chunks))
        en_chunks += [""] * (n - len(en_chunks))

        for k in range(n):
            new_row = []
            for j, cell in enumerate(row):
                if j == pivot:
                    new_row.append({"translated": cn_chunks[k],
                                    "original":   en_chunks[k]})
                else:
                    # 只在第一个子行保留其他列内容
                    new_row.append(cell if k == 0
                                   else {"translated": "", "original": ""})
            result.append(new_row)
    return result


def build_table(trans_rows: list, styles: dict, mode: str, page_w: float):
    """将翻译后的表格数据构建为 reportlab Table（自动处理超长单元格）。"""
    # 预处理：拆分超长行
    trans_rows = _expand_rows(trans_rows, max_cell_chars=700)

    if not trans_rows:
        return None

    col_count = max(len(r) for r in trans_rows)
    col_w = page_w / col_count

    rows = []
    for row in trans_rows:
        cells = []
        for cell in row:
            cn = s(cell["translated"])
            en = s(cell["original"])
            cn_sz, en_sz = _cell_font_size(len(cn), len(en), col_w)
            font_name = styles["cell_cn"].fontName

            if mode == "bilingual":
                if cn.strip() or en.strip():
                    markup = (
                        f'<font name="{font_name}" size="{cn_sz}">{cn}</font>'
                        f'<br/><font name="Helvetica" size="{en_sz}" color="#999999">{en}</font>'
                    )
                    p_style = ParagraphStyle("cc", fontName=font_name,
                                             fontSize=cn_sz, leading=cn_sz * 1.4)
                    cells.append(Paragraph(markup, p_style))
                else:
                    cells.append(Paragraph("", styles["cell_cn"]))
            else:
                if cn.strip():
                    p_style = ParagraphStyle("cc", fontName=font_name,
                                             fontSize=cn_sz, leading=cn_sz * 1.4)
                    cells.append(Paragraph(cn, p_style))
                else:
                    cells.append(Paragraph("", styles["cell_cn"]))
        # 填充短行（保证列数一致）
        while len(cells) < col_count:
            cells.append(Paragraph("", styles["cell_cn"]))
        rows.append(cells)

    tbl = Table(rows, colWidths=[col_w] * col_count,
                repeatRows=1, splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#D0E4F5")),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#C0C0C0")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F0F6FF")]),
    ]))
    return tbl


def is_heading(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if t.upper() == t and len(t) > 4:      # 全大写
        return True
    if t.startswith("FACT SHEET"):
        return True
    if len(t) < 80 and t[:2] in ("A.", "B.", "C.", "D.", "E.", "F.", "G."):
        return True
    return False


def build_elements(content: list, font: str, mode: str) -> list:
    """将翻译内容转换为 reportlab Flowable 列表。"""
    styles  = make_styles(font)
    # A4宽 - 左右页边距(各1.5cm) - 框架内边距(各6pt) ≈ 498pt
    page_w = A4[0] - 2 * 1.5 * cm - 12
    elements = []

    for item in content:
        if item["type"] == "table":
            tbl = build_table(item["data"], styles, mode, page_w)
            if tbl:
                elements.append(tbl)
                elements.append(Spacer(1, 0.35 * cm))

        else:  # text
            orig_lines  = item["original"].split("\n")
            trans_lines = item["translated"].split("\n")

            # 行数对齐
            n = max(len(orig_lines), len(trans_lines))
            orig_lines  += [""] * (n - len(orig_lines))
            trans_lines += [""] * (n - len(trans_lines))

            for orig, trans in zip(orig_lines, trans_lines):
                orig  = orig.strip()
                trans = trans.strip()
                if not orig and not trans:
                    continue

                if is_heading(orig):
                    if mode == "bilingual":
                        elements.append(Paragraph(s(trans), styles["h2"]))
                        elements.append(Paragraph(s(orig),  styles["body_en"]))
                    else:
                        elements.append(Paragraph(s(trans), styles["h2"]))
                else:
                    if mode == "bilingual":
                        if trans:
                            elements.append(Paragraph(s(trans), styles["body_cn"]))
                        if orig:
                            elements.append(Paragraph(s(orig),  styles["body_en"]))
                    else:
                        if trans:
                            elements.append(Paragraph(s(trans), styles["body_cn"]))
                elements.append(Spacer(1, 0.05 * cm))

            elements.append(Spacer(1, 0.25 * cm))

    return elements


def write_pdf(elements: list, out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
    )
    doc.build(elements)
    kb = os.path.getsize(out_path) / 1024
    print(f"  ✓ 已生成: {out_path}  ({kb:.0f} KB)")


# ═══════════════════════════════════════════════════════
#  6. 主程序入口
# ═══════════════════════════════════════════════════════

def main():
    if len(sys.argv) >= 2:
        pdf_path = sys.argv[1]
    else:
        # 自动查找当前目录唯一 PDF
        pdfs = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
        if len(pdfs) == 1:
            pdf_path = pdfs[0]
            print(f"  自动检测到 PDF: {pdf_path}")
        else:
            print("用法: python3 translate_pdf.py <input.pdf>")
            sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"✗ 文件不存在: {pdf_path}")
        sys.exit(1)

    print("=" * 55)
    print("   PDF 翻译工具  ·  英文 → 中文")
    print("=" * 55)

    # Step 1: 字体
    print("\n[1/5] 配置中文字体…")
    font = setup_fonts()

    # Step 2: 提取
    print("\n[2/5] 提取 PDF 内容…")
    content = extract_pdf(pdf_path)
    print(f"  共提取 {len(content)} 个内容块")

    # Step 3: 翻译（支持缓存）
    cache_path = os.path.splitext(pdf_path)[0] + "_translation_cache.json"
    if os.path.exists(cache_path):
        print(f"\n[3/5] 发现缓存文件，跳过翻译，直接读取…")
        with open(cache_path, "r", encoding="utf-8") as f:
            translated = json.load(f)
    else:
        print("\n[3/5] 翻译（Google 翻译，请确保网络正常）…")
        translated = translate_all(content)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)
        print(f"  翻译结果已缓存到: {cache_path}")

    base = os.path.splitext(pdf_path)[0]

    # Step 4: 双语 PDF
    print("\n[4/5] 生成双语 PDF（中英对照）…")
    bilingual = build_elements(translated, font, mode="bilingual")
    write_pdf(bilingual, f"{base}_双语版.pdf")

    # Step 5: 纯中文 PDF
    print("\n[5/5] 生成纯中文 PDF…")
    chinese = build_elements(translated, font, mode="chinese")
    write_pdf(chinese, f"{base}_中文版.pdf")

    print("\n" + "=" * 55)
    print("  完成！")
    print(f"  双语版 → {base}_双语版.pdf")
    print(f"  中文版 → {base}_中文版.pdf")
    print("=" * 55)


if __name__ == "__main__":
    main()
