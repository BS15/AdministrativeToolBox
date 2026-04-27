"""Extração de relatório SISCAC e geração de lista de pagamentos em CSV.

Ported from BS15/djangoproject pagamentos/utils.py – sem dependências Django.
Compatível com PyScript/Pyodide: aceita bytes ou BytesIO além de caminho de arquivo.
"""

import csv
import io
import re
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader


# ---------------------------------------------------------------------------
# Extração do PDF SISCAC
# ---------------------------------------------------------------------------

def parse_siscac_report(pdf_source) -> list[dict]:
    """Lê o relatório SISCAC (PDF) e retorna lista de pagamentos consolidados.

    Args:
        pdf_source: Caminho do arquivo (str/Path), bytes ou BytesIO.

    Cada item do resultado é um dicionário com as chaves:
        siscac_pg    – número do pagamento (ex: 2024PG00123)
        credor       – nome do credor conforme consta no relatório
        nota_empenho – número da nota de empenho (ex: 2024NE00456)
        valor_total  – valor total em Decimal
        comprovante  – número do comprovante bancário ou None
    """
    pattern_payment = re.compile(
        r'^(20\d{2}PG\d{5})\s+(.*?)\s+(20\d{2}NE\d{5}).*?([\d.,]+)$'
    )
    pattern_comprovante = re.compile(r'N[oº°]\s*do\s*Comprovante[:\s]*([\d.\-]+)', re.IGNORECASE)

    payments: dict[str, dict] = {}
    current_comprovante: str | None = None

    if isinstance(pdf_source, bytes):
        pdf_source = io.BytesIO(pdf_source)

    reader = PdfReader(pdf_source)
    for page in reader.pages:
        text = page.extract_text() or ''
        for line in text.splitlines():
            m_comp = pattern_comprovante.search(line)
            if m_comp:
                current_comprovante = m_comp.group(1).replace('.', '')

            m_pay = pattern_payment.match(line)
            if m_pay:
                pg = m_pay.group(1)
                credor = m_pay.group(2).strip()
                nota_empenho = m_pay.group(3)
                valor_str = m_pay.group(4)
                valor_decimal = Decimal(valor_str.replace('.', '').replace(',', '.'))

                if pg in payments:
                    payments[pg]['valor_total'] += valor_decimal
                else:
                    payments[pg] = {
                        'siscac_pg': pg,
                        'credor': credor,
                        'nota_empenho': nota_empenho,
                        'valor_total': valor_decimal,
                        'comprovante': current_comprovante,
                    }

    return list(payments.values())


# ---------------------------------------------------------------------------
# Geração de CSV
# ---------------------------------------------------------------------------

FIELDNAMES = [
    'siscac_pg',
    'credor',
    'nota_empenho',
    'valor_total',
    'comprovante',
]


def payments_to_csv(payments: list[dict], output_path: str | Path) -> Path:
    """Escreve a lista de pagamentos em um arquivo CSV (uso via CLI).

    Args:
        payments:    Lista retornada por parse_siscac_report.
        output_path: Caminho do arquivo CSV de saída.

    Returns:
        Path para o arquivo CSV gerado.
    """
    output_path = Path(output_path)
    with output_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
        writer.writeheader()
        for row in payments:
            writer.writerow({
                **row,
                'valor_total': f"{row['valor_total']:.2f}".replace('.', ','),
            })
    return output_path


def payments_to_csv_string(payments: list[dict]) -> str:
    """Retorna a lista de pagamentos como string CSV com BOM UTF-8.

    Adequado para uso no browser (PyScript): não escreve em disco.
    O BOM garante compatibilidade com Excel ao abrir o CSV.

    Args:
        payments: Lista retornada por parse_siscac_report.

    Returns:
        String CSV com BOM (\\ufeff) no início.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDNAMES, extrasaction='ignore')
    writer.writeheader()
    for row in payments:
        writer.writerow({
            **row,
            'valor_total': f"{row['valor_total']:.2f}".replace('.', ','),
        })
    return '\ufeff' + buf.getvalue()


def generate_payments_csv(pdf_path: str | Path, output_path: str | Path) -> Path:
    """Pipeline completo: lê o PDF SISCAC e grava o CSV de pagamentos.

    Args:
        pdf_path:    Caminho do relatório SISCAC em PDF.
        output_path: Caminho do arquivo CSV de saída.

    Returns:
        Path para o arquivo CSV gerado.
    """
    payments = parse_siscac_report(pdf_path)
    return payments_to_csv(payments, output_path)


__all__ = [
    'parse_siscac_report',
    'payments_to_csv',
    'payments_to_csv_string',
    'generate_payments_csv',
]
