"""Testes unitários para toolbox.siscac_payments."""

import io
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from toolbox.siscac_payments import parse_siscac_report, payments_to_csv, payments_to_csv_string


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_reader(pages_text: list[str]):
    """Cria um mock de PdfReader com as páginas de texto fornecidas."""
    mock_pages = []
    for text in pages_text:
        page = MagicMock()
        page.extract_text.return_value = text
        mock_pages.append(page)

    mock_reader = MagicMock()
    mock_reader.pages = mock_pages
    return mock_reader


SAMPLE_PAGE = """\
Relatório de Pagamentos SISCAC
Nº do Comprovante: 2024.00001
2024PG00001 EMPRESA ALFA LTDA 2024NE00100 OUTROS DADOS 10.500,00
2024PG00002 EMPRESA BETA S/A 2024NE00200 OUTROS DADOS 3.200,50
"""

SAMPLE_PAGE_MULTI = """\
Nº do Comprovante: 2024.00002
2024PG00003 EMPRESA GAMA EIRELI 2024NE00300 OUTROS DADOS 1.000,00
2024PG00003 EMPRESA GAMA EIRELI 2024NE00300 OUTROS DADOS 500,00
"""


# ---------------------------------------------------------------------------
# parse_siscac_report
# ---------------------------------------------------------------------------

@patch('toolbox.siscac_payments.PdfReader')
def test_parse_siscac_report_basic(mock_reader_class):
    mock_reader_class.return_value = _make_fake_reader([SAMPLE_PAGE])

    result = parse_siscac_report(b'fake pdf bytes')

    assert len(result) == 2
    pg_ids = {r['siscac_pg'] for r in result}
    assert '2024PG00001' in pg_ids
    assert '2024PG00002' in pg_ids

    alfa = next(r for r in result if r['siscac_pg'] == '2024PG00001')
    assert alfa['credor'] == 'EMPRESA ALFA LTDA'
    assert alfa['nota_empenho'] == '2024NE00100'
    assert alfa['valor_total'] == Decimal('10500.00')
    assert alfa['comprovante'] == '202400001'


@patch('toolbox.siscac_payments.PdfReader')
def test_parse_siscac_report_accumulates_same_pg(mock_reader_class):
    mock_reader_class.return_value = _make_fake_reader([SAMPLE_PAGE_MULTI])

    result = parse_siscac_report(b'fake pdf bytes')

    assert len(result) == 1
    assert result[0]['valor_total'] == Decimal('1500.00')


@patch('toolbox.siscac_payments.PdfReader')
def test_parse_siscac_report_empty(mock_reader_class):
    mock_reader_class.return_value = _make_fake_reader(['Sem dados relevantes aqui.'])

    result = parse_siscac_report(b'fake pdf bytes')

    assert result == []


@patch('toolbox.siscac_payments.PdfReader')
def test_parse_siscac_report_accepts_bytesio(mock_reader_class):
    mock_reader_class.return_value = _make_fake_reader([SAMPLE_PAGE])

    result = parse_siscac_report(io.BytesIO(b'fake pdf bytes'))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# payments_to_csv
# ---------------------------------------------------------------------------

def test_payments_to_csv_creates_file(tmp_path):
    payments = [
        {
            'siscac_pg': '2024PG00001',
            'credor': 'EMPRESA ALFA LTDA',
            'nota_empenho': '2024NE00100',
            'valor_total': Decimal('10500.00'),
            'comprovante': '202400001',
        }
    ]
    out = tmp_path / 'out.csv'
    result = payments_to_csv(payments, out)

    assert result == out
    content = out.read_text(encoding='utf-8-sig')
    assert 'siscac_pg' in content
    assert '2024PG00001' in content
    assert 'EMPRESA ALFA LTDA' in content
    assert '10500,00' in content


def test_payments_to_csv_header_columns(tmp_path):
    payments = []
    out = tmp_path / 'empty.csv'
    payments_to_csv(payments, out)
    lines = out.read_text(encoding='utf-8-sig').splitlines()
    assert lines[0] == 'siscac_pg,credor,nota_empenho,valor_total,comprovante'


# ---------------------------------------------------------------------------
# payments_to_csv_string (browser / PyScript use)
# ---------------------------------------------------------------------------

def test_payments_to_csv_string_returns_string():
    payments = [
        {
            'siscac_pg': '2024PG00001',
            'credor': 'EMPRESA ALFA LTDA',
            'nota_empenho': '2024NE00100',
            'valor_total': Decimal('10500.00'),
            'comprovante': '202400001',
        }
    ]
    result = payments_to_csv_string(payments)

    assert isinstance(result, str)
    assert result.startswith('\ufeff')  # BOM for Excel
    assert '2024PG00001' in result
    assert '10500,00' in result


def test_payments_to_csv_string_empty():
    result = payments_to_csv_string([])
    assert isinstance(result, str)
    assert 'siscac_pg' in result  # header still present
