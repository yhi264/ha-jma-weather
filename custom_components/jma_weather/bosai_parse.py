"""防災情報の詳細XML(JMX)解析（HA 非依存の純ロジック）。

JMX は名前空間付きだが、製品ごとに異なるため、要素はローカル名で走査する。
"""
from __future__ import annotations

import datetime as dt
from typing import Any
from xml.etree.ElementTree import Element  # 型注釈のみ（パースには使わない）

from defusedxml import ElementTree as ET  # 安全なパーサ（fromstring）。HA core 非同梱のため依存に明示済

from .const import KIROKU_AME_VALID_SEC, TATSUMAKI_FALLBACK_VALID_SEC


def _local(tag: str) -> str:
    """名前空間付きタグからローカル名を取り出す。"""
    return tag.rsplit("}", 1)[-1]


def _find_head(root: Element) -> Element:
    """Head 要素を返す（無ければ root）。Title 等が Control と Head の両方に出るため、
    Head 配下に限定して探すのに使う。"""
    for el in root.iter():
        if _local(el.tag) == "Head":
            return el
    return root


def _find_text(root: Element, localname: str) -> str:
    """最初に一致するローカル名要素のテキストを返す（深さ優先・全走査）。"""
    for el in root.iter():
        if _local(el.tag) == localname and el.text:
            return el.text.strip()
    return ""


def _iter_local(root: Element, localname: str):
    for el in root.iter():
        if _local(el.tag) == localname:
            yield el


def _parse_dt(s: str) -> dt.datetime | None:
    s = s.strip()
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def _area_codes(root: Element) -> list[tuple[str, str]]:
    """全 Area 要素の (name, code) を返す。"""
    out: list[tuple[str, str]] = []
    for area in _iter_local(root, "Area"):
        name = ""
        code = ""
        for child in area:
            ln = _local(child.tag)
            if ln == "Name" and child.text:
                name = child.text.strip()
            elif ln == "Code" and child.text:
                code = child.text.strip()
        if code:
            out.append((name, code))
    return out


def parse_doshakei(xml_text: str, class20_code: str) -> dict[str, Any]:
    """土砂災害警戒情報。Kind/Name=="警戒" の Item の対象市町村に class20 が含まれ、
    かつ取消でなければ active。

    実 VXWW50 は県内全市町村を Item として列挙し、各 Item の Kind/Name で
    警戒/なし/解除 を区別する（「Area に列挙＝警戒」ではない）。
    """
    root = ET.fromstring(xml_text)
    head = _find_head(root)
    info_type = _find_text(head, "InfoType")
    report_dt = _find_text(head, "ReportDateTime")
    headline = _find_text(head, "Text")

    warned: list[tuple[str, str]] = []
    for item in _iter_local(root, "Item"):
        # この Item の Kind/Name
        kind_name = ""
        for kind in _iter_local(item, "Kind"):
            for c in kind.iter():
                if _local(c.tag) == "Name" and c.text:
                    kind_name = c.text.strip()
                    break
            break
        if kind_name != "警戒":
            continue
        # この Item 配下の Area（Areas/Area でも Area 直下でも可）
        for area in _iter_local(item, "Area"):
            a_name = a_code = ""
            for c in area:
                ln = _local(c.tag)
                if ln == "Name" and c.text:
                    a_name = c.text.strip()
                elif ln == "Code" and c.text:
                    a_code = c.text.strip()
            if a_code:
                warned.append((a_name, a_code))

    target_codes = {c for _n, c in warned}
    seen: set[str] = set()
    target_names: list[str] = []
    for n, c in warned:
        if n and c not in seen:
            seen.add(c)
            target_names.append(n)

    active = (info_type != "取消") and (class20_code in target_codes)
    return {
        "active": active,
        "info_type": info_type,
        "report_datetime": report_dt,
        "headline": headline,
        "target_areas": target_names,
    }


def parse_tatsumaki(
    xml_text: str, office_code: str, now: dt.datetime
) -> dict[str, Any]:
    """竜巻注意情報。発表かつ ValidDateTime 未経過なら active。

    office_code は API 互換のため受け取るが、対象地域の一致判定はフィード側の
    ファイル名 office フィルタ（coordinator が当該 office の文書のみ取得）に委譲している。
    安全側（誤検出による失効漏れ回避）を優先し、ここでは Area の追加絞り込みはしない。
    将来 class10/class20 レベルの精緻化のためにパラメータを保持する。
    """
    root = ET.fromstring(xml_text)
    info_type = _find_text(root, "InfoType")
    report_dt = _find_text(root, "ReportDateTime")
    headline = _find_text(root, "Text")
    valid_s = _find_text(root, "ValidDateTime")
    valid = _parse_dt(valid_s)
    if valid is None:
        rep = _parse_dt(report_dt)
        if rep is not None:
            valid = rep + dt.timedelta(seconds=TATSUMAKI_FALLBACK_VALID_SEC)
    active = (info_type == "発表") and (valid is not None) and (now < valid)
    return {
        "active": active,
        "info_type": info_type,
        "report_datetime": report_dt,
        "valid_until": valid.isoformat() if valid else "",
        "headline": headline,
    }


def parse_kirokuame(xml_text: str, now: dt.datetime) -> dict[str, Any]:
    """記録的短時間大雨情報（府県気象情報のうち見出しに該当語を含むもの）。

    取消電文が無いため ReportDateTime から KIROKU_AME_VALID_SEC 以内なら active。
    """
    root = ET.fromstring(xml_text)
    head = _find_head(root)
    info_type = _find_text(head, "InfoType")
    title = _find_text(head, "Title")
    headline = _find_text(head, "Text")
    report_dt = _find_text(head, "ReportDateTime")
    is_kiroku = ("記録的短時間大雨" in title) or ("記録的短時間大雨" in headline)
    rep = _parse_dt(report_dt)
    within = (
        rep is not None
        and now >= rep
        and (now - rep).total_seconds() <= KIROKU_AME_VALID_SEC
    )
    active = is_kiroku and (info_type != "取消") and within
    return {
        "active": active,
        "info_type": info_type,
        "report_datetime": report_dt,
        "headline": headline if is_kiroku else "",
    }
