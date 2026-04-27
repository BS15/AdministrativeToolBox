"""Testes unitários para toolbox.efdreinf_xml."""

import csv
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from toolbox.efdreinf_xml import (
    _build_fechamento_xml,
    _build_r1000_xml,
    _build_r2010_xml,
    _build_r4020_xml,
    _natureza_rendimento_valida,
    read_control_sheet,
    validate_records,
    gerar_xmls_reinf,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CNPJ_CONTRIB = '12345678000190'
CNPJ_PRESTADOR = '98765432000100'


def _make_sample_xlsx(tmp_path: Path, rows: list[dict]) -> Path:
    """Cria uma planilha de controle mínima para testes."""
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = [
        'CNPJ Emitente', 'Nome Emitente', 'Número NF', 'Série NF',
        'Data Emissão', 'Valor Bruto', 'Código Imposto', 'Série Reinf',
        'Natureza Rendimento', 'Base de Cálculo', 'Valor Retido',
        'CNPJ Beneficiário', 'Nome Beneficiário', 'Tipo Beneficiário',
    ]
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    path = tmp_path / 'controle.xlsx'
    wb.save(path)
    return path


def _make_sample_csv_schema(tmp_path: Path, rows: list[dict]) -> Path:
    headers = [
        'CNPJ',
        'Abreviatura',
        'Data pagto',
        'Natureza rendimento (cód. Ecac)',
        'Cód. Receita (siscac)',
        'Valor tributável',
        'Retenção agregada',
        'Retenção individual',
    ]
    path = tmp_path / 'controle.csv'
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


SAMPLE_INSS_ROW = {
    'CNPJ Emitente': '98.765.432/0001-00',
    'Nome Emitente': 'Prestador INSS Ltda',
    'Número NF': '1001',
    'Série NF': 'A',
    'Data Emissão': date(2024, 6, 1),
    'Valor Bruto': 5000.00,
    'Código Imposto': '2100',
    'Série Reinf': 'S2000',
    'Natureza Rendimento': '',
    'Base de Cálculo': 5000.00,
    'Valor Retido': 550.00,
    'CNPJ Beneficiário': '',
    'Nome Beneficiário': '',
    'Tipo Beneficiário': 'PJ',
}

SAMPLE_FEDERAL_ROW = {
    'CNPJ Emitente': '98.765.432/0001-00',
    'Nome Emitente': 'Prestador Federal Ltda',
    'Número NF': '1002',
    'Série NF': 'A',
    'Data Emissão': date(2024, 6, 2),
    'Valor Bruto': 10000.00,
    'Código Imposto': '1708',
    'Série Reinf': 'S4000',
    'Natureza Rendimento': '15001',
    'Base de Cálculo': 10000.00,
    'Valor Retido': 1500.00,
    'CNPJ Beneficiário': '98.765.432/0001-00',
    'Nome Beneficiário': 'Prestador Federal Ltda',
    'Tipo Beneficiário': 'PJ',
}


# ---------------------------------------------------------------------------
# Validações de natureza rendimento
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('value,expected', [
    ('15001', True),
    ('00000', True),
    ('1234', False),
    ('123456', False),
    ('abcde', False),
    ('', False),
    (None, False),
])
def test_natureza_rendimento_valida(value, expected):
    assert _natureza_rendimento_valida(value) == expected


# ---------------------------------------------------------------------------
# read_control_sheet
# ---------------------------------------------------------------------------

def test_read_control_sheet_inss(tmp_path):
    xlsx = _make_sample_xlsx(tmp_path, [SAMPLE_INSS_ROW])
    records = read_control_sheet(xlsx)

    assert len(records) == 1
    rec = records[0]
    assert rec['serie_reinf'] == 'S2000'
    assert rec['cnpj_emitente'] == '98765432000100'
    assert rec['numero_nf'] == '1001'
    assert rec['valor_bruto'] == Decimal('5000.00')
    assert rec['valor_retido'] == Decimal('550.00')


def test_read_control_sheet_federal(tmp_path):
    xlsx = _make_sample_xlsx(tmp_path, [SAMPLE_FEDERAL_ROW])
    records = read_control_sheet(xlsx)

    assert len(records) == 1
    assert records[0]['serie_reinf'] == 'S4000'
    assert records[0]['natureza_rendimento'] == '15001'


def test_read_control_sheet_skips_invalid_serie(tmp_path):
    bad_row = {**SAMPLE_INSS_ROW, 'Série Reinf': 'S9999'}
    xlsx = _make_sample_xlsx(tmp_path, [bad_row])
    records = read_control_sheet(xlsx)
    assert records == []


def test_read_control_sheet_accepts_csv_schema(tmp_path):
    csv_path = _make_sample_csv_schema(
        tmp_path,
        [
            {
                'CNPJ': '98.765.432/0001-00',
                'Abreviatura': 'Prestador Federal',
                'Data pagto': '05/06/2024',
                'Natureza rendimento (cód. Ecac)': '15001',
                'Cód. Receita (siscac)': '1708',
                'Valor tributável': '10000,00',
                'Retenção agregada': '1500,00',
                'Retenção individual': '1500,00',
            }
        ],
    )

    records = read_control_sheet(csv_path)

    assert len(records) == 1
    rec = records[0]
    assert rec['cnpj_emitente'] == '98765432000100'
    assert rec['nome_emitente'] == 'Prestador Federal'
    assert rec['serie_reinf'] == 'S4000'
    assert rec['natureza_rendimento'] == '15001'
    assert rec['base_calculo'] == Decimal('10000.00')
    assert rec['valor_retido'] == Decimal('1500.00')


# ---------------------------------------------------------------------------
# validate_records
# ---------------------------------------------------------------------------

def test_validate_records_ok():
    records = [
        {
            'cnpj_emitente': CNPJ_PRESTADOR,
            'serie_reinf': 'S2000',
            'natureza_rendimento': '',
            'valor_retido': Decimal('100'),
        },
        {
            'cnpj_emitente': CNPJ_PRESTADOR,
            'serie_reinf': 'S4000',
            'natureza_rendimento': '15001',
            'valor_retido': Decimal('50'),
        },
    ]
    assert validate_records(records) == []


def test_validate_records_missing_cnpj():
    records = [{'cnpj_emitente': '', 'serie_reinf': 'S2000', 'natureza_rendimento': '', 'valor_retido': Decimal('1')}]
    issues = validate_records(records)
    assert any('CNPJ Emitente ausente' in i for i in issues)


def test_validate_records_bad_natureza_s4000():
    records = [{'cnpj_emitente': CNPJ_PRESTADOR, 'serie_reinf': 'S4000',
                'natureza_rendimento': '999', 'valor_retido': Decimal('1')}]
    issues = validate_records(records)
    assert any('Natureza Rendimento' in i for i in issues)


# ---------------------------------------------------------------------------
# XML builders
# ---------------------------------------------------------------------------

def test_build_r1000_xml():
    xml_str = _build_r1000_xml(CNPJ_CONTRIB, 'Empresa Teste Ltda')
    root = ET.fromstring(xml_str.split('\n', 1)[1])  # strip XML declaration
    assert root.tag.endswith('Reinf')
    nr_insc = root.find('.//{*}nrInsc')
    assert nr_insc is not None and nr_insc.text == CNPJ_CONTRIB


def test_build_r2010_xml():
    records = [
        {
            'numero_nf': '1001', 'data_emissao': date(2024, 6, 1), 'valor_bruto': Decimal('5000'),
            'base_calculo': Decimal('5000'), 'valor_retido': Decimal('550'),
        }
    ]
    xml_str = _build_r2010_xml(CNPJ_CONTRIB, CNPJ_PRESTADOR, records, 6, 2024)
    root = ET.fromstring(xml_str.split('\n', 1)[1])
    per_apur = root.find('.//{*}perApur')
    assert per_apur is not None and per_apur.text == '2024-06'
    nr_nf = root.find('.//{*}nrNF')
    assert nr_nf is not None and nr_nf.text == '1001'


def test_build_r4020_xml():
    records = [
        {
            'numero_nf': '1002', 'data_emissao': date(2024, 6, 2), 'valor_bruto': Decimal('10000'),
            'base_calculo': Decimal('10000'), 'valor_retido': Decimal('1500'),
            'natureza_rendimento': '15001',
        }
    ]
    xml_str = _build_r4020_xml(CNPJ_CONTRIB, CNPJ_PRESTADOR, records, 6, 2024)
    root = ET.fromstring(xml_str.split('\n', 1)[1])
    nat_rend = root.find('.//{*}natRend')
    assert nat_rend is not None and nat_rend.text == '15001'


def test_build_fechamento_xml():
    xml_str = _build_fechamento_xml('evtFechaEvPer', '2024-06')
    root = ET.fromstring(xml_str.split('\n', 1)[1])
    per_apur = root.find('.//{*}perApur')
    assert per_apur is not None and per_apur.text == '2024-06'


# ---------------------------------------------------------------------------
# Integration: gerar_lotes_reinf
# ---------------------------------------------------------------------------

def test_gerar_lotes_reinf_generates_files(tmp_path):
    from toolbox.efdreinf_xml import gerar_lotes_reinf

    xlsx = _make_sample_xlsx(tmp_path, [SAMPLE_INSS_ROW, SAMPLE_FEDERAL_ROW])
    out_dir = tmp_path / 'output'

    generated = gerar_lotes_reinf(
        xlsx_path=xlsx,
        cnpj_contribuinte=CNPJ_CONTRIB,
        razao_social='Empresa Teste Ltda',
        month=6,
        year=2024,
        output_dir=out_dir,
    )

    assert 'R-1000_Cadastro_Empresa.xml' in generated
    assert any('R2010' in k for k in generated)
    assert any('R4020' in k for k in generated)
    assert any('R2099' in k for k in generated)
    assert any('R4099' in k for k in generated)

    for path in generated.values():
        assert path.exists()
        assert path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Integration: gerar_xmls_reinf (browser / PyScript use)
# ---------------------------------------------------------------------------

def test_gerar_xmls_reinf_returns_strings(tmp_path):
    xlsx = _make_sample_xlsx(tmp_path, [SAMPLE_INSS_ROW, SAMPLE_FEDERAL_ROW])

    xmls = gerar_xmls_reinf(
        xlsx_source=xlsx,
        cnpj_contribuinte=CNPJ_CONTRIB,
        razao_social='Empresa Teste Ltda',
        month=6,
        year=2024,
    )

    assert isinstance(xmls, dict)
    assert 'R-1000_Cadastro_Empresa.xml' in xmls
    assert any('R2010' in k for k in xmls)
    assert any('R4020' in k for k in xmls)
    for content in xmls.values():
        assert isinstance(content, str)
        assert '<?xml' in content


def test_gerar_xmls_reinf_accepts_bytesio(tmp_path):
    import io as _io
    xlsx_path = _make_sample_xlsx(tmp_path, [SAMPLE_INSS_ROW])
    xlsx_bytes = xlsx_path.read_bytes()

    xmls = gerar_xmls_reinf(
        xlsx_source=_io.BytesIO(xlsx_bytes),
        cnpj_contribuinte=CNPJ_CONTRIB,
        razao_social='Empresa Teste Ltda',
        month=6,
        year=2024,
    )

    assert 'R-1000_Cadastro_Empresa.xml' in xmls
    assert any('R2010' in k for k in xmls)
