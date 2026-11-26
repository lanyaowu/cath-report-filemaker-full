#!/usr/bin/env python3
"""PostgreSQL 版スキーマ（Flyway V1__init.sql）から ER 図を生成する。

出力: docs/er_postgres.dot / .svg / .png
使い方: python3 tools/gen_pg_er.py   （Graphviz の dot が必要）
"""
import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "backend-spring-pg/src/main/resources/db/migration/V1__init.sql"
OUT = ROOT / "docs"

LABELS = {
    "patients": "患者",
    "patient_admissions": "病歴総括",
    "cath_reports": "カテレポート",
    "report_history": "登録履歴",
    "report_mace": "MACE",
    "report_images": "画像メタ情報",
    "report_image_data": "画像本体",
    "master_items": "マスタ",
}
COLORS = {"patients": "#dcebe2", "cath_reports": "#dcebe2", "master_items": "#ececec"}


def parse(sql: str):
    tables = {}
    for m in re.finditer(r"CREATE TABLE (\w+) \((.*?)\n\);", sql, re.S):
        name, body = m.group(1), m.group(2)
        cols, pk, fks = [], set(), []
        for raw in body.split("\n"):
            line = raw.strip()
            if not line or line.startswith("--"):
                continue
            comment = ""
            if "--" in line:
                line, comment = line.split("--", 1)
                line, comment = line.strip(), comment.strip()
            line = line.rstrip(",")
            pkm = re.match(r"PRIMARY KEY \((.*?)\)", line)
            if pkm:
                pk |= {c.strip() for c in pkm.group(1).split(",")}
                continue
            if line.startswith("CONSTRAINT"):
                continue
            cm = re.match(r"(\w+)\s+([A-Z]+(?:\(\d+\))?)(.*)", line)
            if not cm:
                continue
            col, typ, rest = cm.groups()
            if "PRIMARY KEY" in rest:
                pk.add(col)
            ref = re.search(r"REFERENCES (\w+)\((\w+)\)(.*)", rest)
            if ref:
                fks.append((col, ref.group(1), "CASCADE" in ref.group(3)))
            cols.append((col, typ.lower(), "NOT NULL" in rest or "PRIMARY KEY" in rest, comment))
        tables[name] = (cols, pk, fks)
    return tables


def font(text, **attrs):
    a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"<FONT {a}>{html.escape(text) if text else ' '}</FONT>"


def dot(tables) -> str:
    out = [
        "digraph ER {",
        '  graph [rankdir=LR, splines=polyline, nodesep=0.5, ranksep=1.1, fontname="Noto Sans CJK JP", bgcolor="#ffffff",',
        '         label="心カテーテルレポート PostgreSQL スキーマ（Flyway V1）", labelloc=t, fontsize=20];',
        '  node [shape=plaintext, fontname="Noto Sans CJK JP"];',
        '  edge [color="#557766", arrowhead=crow, arrowtail=teetee, dir=both, penwidth=1.3];',
    ]
    for name, (cols, pk, fks) in tables.items():
        fkcols = {c for c, _, _ in fks}
        head = COLORS.get(name, "#e8f0ec")
        rows = [
            f'<TR><TD BGCOLOR="{head}" COLSPAN="3">{font(name, **{"POINT-SIZE": "14"})}<BR/>'
            f'{font(LABELS.get(name, ""), **{"POINT-SIZE": "11", "COLOR": "#335544"})}</TD></TR>'
        ]
        for col, typ, nn, comment in cols:
            key = "PK" if col in pk else ("FK" if col in fkcols else "")
            if col in pk and col in fkcols:
                key = "PK,FK"
            is_json = typ == "jsonb"
            color = "#7a4a00" if is_json else "#222222"
            rows.append(
                f'<TR><TD ALIGN="LEFT" PORT="{col}">{font(col, COLOR=color)}</TD>'
                f'<TD ALIGN="LEFT">{font(typ + ("" if nn else "?"), COLOR="#667766", **{"POINT-SIZE": "10"})}</TD>'
                f'<TD ALIGN="LEFT">{font(key, COLOR="#aa2222", **{"POINT-SIZE": "10"})}</TD></TR>'
            )
        out.append(
            f'  {name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#8aa898" BGCOLOR="#ffffff">'
            + "".join(rows)
            + "</TABLE>>];"
        )
    for name, (_, _, fks) in tables.items():
        for col, ref, cascade in fks:
            style = "solid" if cascade else "dashed"
            out.append(f'  {ref} -> {name} [style={style}, xlabel="{"CASCADE" if cascade else "RESTRICT"}", fontsize=9, fontcolor="#668877"];')
    out.append(
        '  legend [label=<<TABLE BORDER="0" CELLSPACING="2">'
        f'<TR><TD ALIGN="LEFT">{font("凡例", **{"POINT-SIZE": "12"})}</TD></TR>'
        f'<TR><TD ALIGN="LEFT">{font("茶色の列 = JSONB（画面ごとの詳細項目）", COLOR="#7a4a00", **{"POINT-SIZE": "10"})}</TD></TR>'
        f'<TR><TD ALIGN="LEFT">{font("型の後ろの ? = NULL 可", **{"POINT-SIZE": "10"})}</TD></TR>'
        f'<TR><TD ALIGN="LEFT">{font("実線 = ON DELETE CASCADE / 破線 = RESTRICT", **{"POINT-SIZE": "10"})}</TD></TR>'
        "</TABLE>>];"
    )
    out.append("}")
    return "\n".join(out)


def main():
    tables = parse(SQL.read_text(encoding="utf-8"))
    d = dot(tables)
    (OUT / "er_postgres.dot").write_text(d, encoding="utf-8")
    for fmt, extra in (("svg", []), ("png", ["-Gdpi=150"])):
        subprocess.run(["dot", f"-T{fmt}", *extra, "-o", str(OUT / f"er_postgres.{fmt}"), str(OUT / "er_postgres.dot")], check=True)
    print("tables:", ", ".join(tables))


if __name__ == "__main__":
    main()
