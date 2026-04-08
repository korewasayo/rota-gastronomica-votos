import sys
import os
import glob
import re
from collections import Counter
from datetime import datetime

import chardet
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)

# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
COLUNAS = {
    "timestamp": ["timestamp", "data", "date"],
    "email":     ["email address", "email", "e-mail"],
    "prato":     ["escolha o seu prato favorito:", "prato", "dish", "escolha"],
    "consent":   ["consentimento", "consent"],
}

AZUL_ESCURO  = colors.HexColor("#16213e")
AZUL_MED     = colors.HexColor("#0f3460")
VERMELHO     = colors.HexColor("#e94560")
CINZA_CLARO  = colors.HexColor("#f5f5f5")
CINZA_LINHA  = colors.HexColor("#cccccc")
AZUL_ROW     = colors.HexColor("#e8f4fd")
AMARELO_1    = colors.HexColor("#fff3cd")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def detectar_encoding(path):
    with open(path, "rb") as f:
        raw = f.read(8192)
    result = chardet.detect(raw)
    enc = result.get("encoding") or "utf-8"
    enc = enc.replace("ISO-8859-1", "latin-1").replace("Windows-1252", "cp1252")
    return enc


def ler_csv(path):
    enc = detectar_encoding(path)
    for encoding in [enc, "utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            df = pd.read_csv(path, encoding=encoding, on_bad_lines="skip")
            return df, encoding
        except Exception:
            continue
    raise ValueError(f"Nao foi possivel ler {path}")


def normalizar_coluna(df, candidatos):
    for col in df.columns:
        col_norm = col.strip().lower()
        for cand in candidatos:
            if cand in col_norm or col_norm in cand:
                return col
    return None


def nome_restaurante(path):
    """
    extrai o nome limpo do restaurante a partir do nome do ficheiro.
    ex: 'Submissoes Feitas - Restaurante À do Pinto' -> 'Restaurante À do Pinto'
    """
    base = os.path.basename(path)
    nome = os.path.splitext(base)[0]
    # se o nome tiver " - ", apanha tudo depois do primeiro traço
    if " - " in nome:
        nome = nome.split(" - ", 1)[1]
    return nome.strip() or base


# ---------------------------------------------------------------------------
# processamento
# ---------------------------------------------------------------------------

def processar_ficheiro(path):
    df, enc = ler_csv(path)

    col_prato = normalizar_coluna(df, COLUNAS["prato"])
    col_email = normalizar_coluna(df, COLUNAS["email"])

    if col_prato is None:
        print(f"  AVISO: Coluna de prato nao encontrada em: {path}")
        return None

    pratos = df[col_prato].dropna().str.strip()
    contagem = Counter(pratos)
    total = sum(contagem.values())
    emails_unicos = df[col_email].dropna().nunique() if col_email else "N/D"
    ranking = sorted(contagem.items(), key=lambda x: x[1], reverse=True)

    return {
        "restaurante": nome_restaurante(path),
        "ficheiro": os.path.basename(path),
        "encoding": enc,
        "total_votos": total,
        "emails_unicos": emails_unicos,
        "ranking": ranking,
        "vencedor": ranking[0] if ranking else ("—", 0),
    }


def processar_todos(paths):
    resultados = []
    for p in paths:
        print(f"A processar: {p}")
        r = processar_ficheiro(p)
        if r:
            resultados.append(r)
            print(f"  OK | {r['total_votos']} votos | Vencedor: {r['vencedor'][0]} ({r['vencedor'][1]} votos)")
        else:
            print(f"  Ignorado.")
    return resultados


# ---------------------------------------------------------------------------
# exportar para csv
# ---------------------------------------------------------------------------

def exportar_csv(resultados, out_path):
    rows = []
    for r in resultados:
        for pos, (prato, votos) in enumerate(r["ranking"], start=1):
            pct = round(votos / r["total_votos"] * 100, 1) if r["total_votos"] else 0
            rows.append({
                "Restaurante": r["restaurante"],
                "Posicao": pos,
                "Prato": prato,
                "Votos": votos,
                "Percentagem": f"{pct}%",
                "Total Votos Restaurante": r["total_votos"],
                "Vencedor": "Sim" if pos == 1 else "",
            })
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nCSV exportado -> {out_path}")


# ---------------------------------------------------------------------------
# exportar para pdf
# ---------------------------------------------------------------------------

def exportar_pdf(resultados, out_path):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"],
        fontSize=22, spaceAfter=6,
        textColor=AZUL_ESCURO,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#555555"),
        spaceAfter=16,
    )
    rest_style = ParagraphStyle(
        "RestStyle", parent=styles["Heading2"],
        fontSize=14, textColor=AZUL_ESCURO,
        spaceBefore=14, spaceAfter=4,
    )
    winner_style = ParagraphStyle(
        "WinnerStyle", parent=styles["Normal"],
        fontSize=11, textColor=VERMELHO, spaceAfter=4,
    )
    note_style = ParagraphStyle(
        "NoteStyle", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#888888"),
        spaceAfter=10,
    )
    # estilos para texto dentro das células da tabela
    cell_normal = ParagraphStyle(
        "CellNormal", parent=styles["Normal"],
        fontSize=9, leading=12,
    )
    cell_bold = ParagraphStyle(
        "CellBold", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
    )
    cell_header = ParagraphStyle(
        "CellHeader", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    cell_center = ParagraphStyle(
        "CellCenter", parent=styles["Normal"],
        fontSize=9, leading=12, alignment=1,  # 1 = centro
    )
    cell_bold_center = ParagraphStyle(
        "CellBoldCenter", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold", alignment=1,
    )
    cell_header_center = ParagraphStyle(
        "CellHeaderCenter", parent=styles["Normal"],
        fontSize=9, leading=12, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=1,
    )

    # cabeçalho 
    story.append(Paragraph("Ranking de Restaurantes", title_style))
    story.append(Paragraph(
        f"Relatorio gerado em {datetime.now().strftime('%d/%m/%Y as %H:%M')}"
        f"  |  {len(resultados)} restaurante(s) processado(s)",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=VERMELHO, spaceAfter=18))

    # resumo geral.. 
    if len(resultados) > 1:
        story.append(Paragraph("Resumo Geral", styles["Heading2"]))
        story.append(Spacer(1, 6))

        resumo_data = [[
            Paragraph("#", cell_header_center),
            Paragraph("Restaurante", cell_header),
            Paragraph("Votos", cell_header_center),
            Paragraph("Prato Vencedor", cell_header),
            Paragraph("Votos", cell_header_center),
        ]]
        ordenados = sorted(resultados, key=lambda x: x["total_votos"], reverse=True)
        for pos, r in enumerate(ordenados, start=1):
            is_first = (pos == 1)
            cs  = cell_bold        if is_first else cell_normal
            csc = cell_bold_center if is_first else cell_center
            resumo_data.append([
                Paragraph(str(pos),              csc),
                Paragraph(r["restaurante"],       cs),
                Paragraph(str(r["total_votos"]), csc),
                Paragraph(r["vencedor"][0],       cs),
                Paragraph(str(r["vencedor"][1]), csc),
            ])

        col_widths = [0.8*cm, 5.5*cm, 1.8*cm, 6*cm, 1.7*cm]
        t = Table(resumo_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), AZUL_ESCURO),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [CINZA_CLARO, colors.white]),
            ("BACKGROUND",    (0, 1), (-1, 1), AMARELO_1),
            ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_LINHA),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))
        story.append(PageBreak())

    # detalhes por restaurante
    story.append(Paragraph("Detalhe por Restaurante", styles["Heading1"]))
    story.append(Spacer(1, 10))

    ordenados = sorted(resultados, key=lambda x: x["total_votos"], reverse=True)

    for idx, r in enumerate(ordenados):
        story.append(Paragraph(r["restaurante"], rest_style))
        story.append(Paragraph(
            f"Prato vencedor: <b>{r['vencedor'][0]}</b>"
            f" — {r['vencedor'][1]} voto(s)",
            winner_style
        ))
        story.append(Paragraph(
            f"Total de votos: {r['total_votos']}   |   Ficheiro: {r['ficheiro']}",
            note_style
        ))

        if not r["ranking"]:
            story.append(Paragraph("Sem votos registados..", styles["Normal"]))
        else:
            table_data = [[
                Paragraph("Pos.", cell_header_center),
                Paragraph("Prato", cell_header),
                Paragraph("Votos", cell_header_center),
                Paragraph("%", cell_header_center),
            ]]
            for pos, (prato, votos) in enumerate(r["ranking"], start=1):
                pct = round(votos / r["total_votos"] * 100, 1) if r["total_votos"] else 0
                is_first = (pos == 1)
                cs  = cell_bold        if is_first else cell_normal
                csc = cell_bold_center if is_first else cell_center
                table_data.append([
                    Paragraph(str(pos),      csc),
                    Paragraph(prato,          cs),
                    Paragraph(str(votos),    csc),
                    Paragraph(f"{pct}%",     csc),
                ])

            col_widths = [1.2*cm, 9.5*cm, 2*cm, 2*cm]
            t = Table(table_data, colWidths=col_widths)

            ts_styles = [
                ("BACKGROUND",    (0, 0), (-1, 0), AZUL_MED),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [AZUL_ROW, colors.white]),
                ("GRID",          (0, 0), (-1, -1), 0.5, CINZA_LINHA),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
            if len(table_data) > 1:
                ts_styles.append(("BACKGROUND", (0, 1), (-1, 1), AMARELO_1))

            t.setStyle(TableStyle(ts_styles))
            story.append(t)

        if idx < len(ordenados) - 1:
            story.append(Spacer(1, 20))
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#dddddd"), spaceAfter=10
            ))

    doc.build(story)
    print(f"PDF exportado -> {out_path}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if len(args) == 1 and os.path.isdir(args[0]):
            paths = sorted(glob.glob(os.path.join(args[0], "*.csv")))
        else:
            paths = args
    else:
        paths = sorted(glob.glob("*.csv"))

    if not paths:
        print("Nenhum ficheiro CSV encontrado")
        print("Uso: python processar_votos.py [pasta_ou_ficheiros]")
        sys.exit(1)

    print(f"\nEncontrados {len(paths)} ficheiro(s) CSV\n" + "-"*50)
    resultados = processar_todos(paths)

    if not resultados:
        print("Nenhum resultado para exportar..")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_out = f"ranking_restaurantes_{ts}.csv"
    pdf_out = f"ranking_restaurantes_{ts}.pdf"

    print("\n" + "-"*50 + "\nA exportar resultados...\n")
    exportar_csv(resultados, csv_out)
    exportar_pdf(resultados, pdf_out)

    print(f"\nConcluido!!")
    print(f"  CSV -> {csv_out}")
    print(f"  PDF -> {pdf_out}\n")


if __name__ == "__main__":
    main()