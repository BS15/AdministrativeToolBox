"""Geração de lotes XML EFD-Reinf a partir de planilha de controle.

Ported from BS15/djangoproject fiscal/services/reinf.py – sem dependências Django.

Formato esperado da planilha de controle (Excel .xlsx):
    Aba padrão (primeira aba) com as seguintes colunas (nomes exatos ou aproximados):

    Coluna                  | Descrição
    ----------------------- | ------------------------------------------------
    CNPJ Emitente           | CNPJ do prestador de serviço (somente dígitos ou formatado)
    Nome Emitente           | Razão social do prestador
    Número NF               | Número da nota fiscal
    Série NF                | Série da nota fiscal (opcional)
    Data Emissão            | Data de emissão da NF (date ou string DD/MM/AAAA)
    Valor Bruto             | Valor bruto da NF (numérico)
    Código Imposto          | Código de receita / imposto
    Série Reinf             | S2000 (INSS) ou S4000 (Federal IRRF/CSRF)
    Natureza Rendimento     | Código de 5 dígitos – obrigatório para S4000
    Base de Cálculo         | Base de cálculo / rendimento tributável
    Valor Retido            | Valor do imposto retido
    CNPJ Beneficiário       | CNPJ/CPF do beneficiário (usado em S4000; pode ser igual ao Emitente)
    Nome Beneficiário       | Nome do beneficiário (usado em S4000)
    Tipo Beneficiário       | PF ou PJ (usado em S4000 para escolher R-4010 ou R-4020)
"""

import io
import re
import xml.dom.minidom
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import openpyxl


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _fmt_dec(value) -> str:
    """Formata valores decimais no padrão XML fiscal com 2 casas."""
    return f"{Decimal(value or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def _digits_only(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _natureza_rendimento_valida(natureza: str | None) -> bool:
    return bool(re.fullmatch(r"\d{5}", str(natureza or "")))


def _prettify(root: ET.Element) -> str:
    raw = ET.tostring(root, encoding='unicode')
    return xml.dom.minidom.parseString(raw).toprettyxml(indent='  ')


# ---------------------------------------------------------------------------
# Leitura da planilha de controle
# ---------------------------------------------------------------------------

# Mapeamento flexível: aceita variações de nome de coluna
_COL_ALIASES: dict[str, list[str]] = {
    'cnpj_emitente':      ['cnpj emitente', 'cnpj_emitente', 'cnpj prestador', 'cnpj do prestador'],
    'nome_emitente':      ['nome emitente', 'nome_emitente', 'razão social', 'razao social', 'prestador'],
    'numero_nf':          ['número nf', 'numero nf', 'numero_nf', 'nf', 'número da nf', 'nota fiscal'],
    'serie_nf':           ['série nf', 'serie nf', 'serie_nf', 'série da nf'],
    'data_emissao':       ['data emissão', 'data emissao', 'data_emissao', 'emissão', 'emissao'],
    'valor_bruto':        ['valor bruto', 'valor_bruto', 'vr bruto', 'bruto'],
    'codigo_imposto':     ['código imposto', 'codigo imposto', 'codigo_imposto', 'código de receita', 'código'],
    'serie_reinf':        ['série reinf', 'serie reinf', 'serie_reinf', 'série reinf'],
    'natureza_rendimento':['natureza rendimento', 'natureza_rendimento', 'natureza', 'nat rendimento', 'nat. rendimento'],
    'base_calculo':       ['base de cálculo', 'base de calculo', 'base_calculo', 'rendimento tributável',
                           'rendimento tributavel', 'base calculo'],
    'valor_retido':       ['valor retido', 'valor_retido', 'vr retido', 'imposto retido'],
    'cnpj_beneficiario':  ['cnpj beneficiário', 'cnpj beneficiario', 'cnpj_beneficiario', 'cpf/cnpj beneficiário'],
    'nome_beneficiario':  ['nome beneficiário', 'nome beneficiario', 'nome_beneficiario', 'beneficiário', 'beneficiario'],
    'tipo_beneficiario':  ['tipo beneficiário', 'tipo beneficiario', 'tipo_beneficiario', 'pf/pj', 'tipo'],
}


def _resolve_columns(header_row: list[str]) -> dict[str, int]:
    """Mapeia nomes canônicos de coluna para índice na planilha."""
    normalized = [str(h or '').strip().lower() for h in header_row]
    mapping: dict[str, int] = {}
    for canonical, aliases in _COL_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[canonical] = normalized.index(alias)
                break
    return mapping


def _parse_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_decimal(value) -> Decimal:
    if value is None:
        return Decimal('0')
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = str(value).strip().replace(' ', '')
    # Handle Brazilian decimal format (1.234,56)
    if re.match(r'^\d{1,3}(\.\d{3})+(,\d+)?$', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    try:
        return Decimal(s)
    except Exception:
        return Decimal('0')


def read_control_sheet(xlsx_source) -> list[dict]:
    """Lê a planilha de controle e retorna lista de registros normalizados.

    Args:
        xlsx_source: Caminho do arquivo .xlsx (str/Path), bytes ou BytesIO.

    Returns:
        Lista de dicionários com chaves canônicas conforme _COL_ALIASES.
    """
    if isinstance(xlsx_source, bytes):
        xlsx_source = io.BytesIO(xlsx_source)
    wb = openpyxl.load_workbook(xlsx_source, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    header = list(rows[0])
    col_map = _resolve_columns(header)

    def _get(row, key):
        idx = col_map.get(key)
        return row[idx] if idx is not None and idx < len(row) else None

    records = []
    for row in rows[1:]:
        serie_reinf = str(_get(row, 'serie_reinf') or '').strip().upper()
        if serie_reinf not in ('S2000', 'S4000'):
            continue

        record = {
            'cnpj_emitente':       _digits_only(_get(row, 'cnpj_emitente')),
            'nome_emitente':       str(_get(row, 'nome_emitente') or '').strip(),
            'numero_nf':           str(_get(row, 'numero_nf') or '').strip(),
            'serie_nf':            str(_get(row, 'serie_nf') or '').strip(),
            'data_emissao':        _parse_date(_get(row, 'data_emissao')),
            'valor_bruto':         _parse_decimal(_get(row, 'valor_bruto')),
            'codigo_imposto':      str(_get(row, 'codigo_imposto') or '').strip(),
            'serie_reinf':         serie_reinf,
            'natureza_rendimento': str(_get(row, 'natureza_rendimento') or '').strip(),
            'base_calculo':        _parse_decimal(_get(row, 'base_calculo')),
            'valor_retido':        _parse_decimal(_get(row, 'valor_retido')),
            'cnpj_beneficiario':   _digits_only(_get(row, 'cnpj_beneficiario')),
            'nome_beneficiario':   str(_get(row, 'nome_beneficiario') or '').strip(),
            'tipo_beneficiario':   str(_get(row, 'tipo_beneficiario') or 'PJ').strip().upper(),
        }
        records.append(record)

    wb.close()
    return records


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def validate_records(records: list[dict]) -> list[str]:
    """Valida registros e retorna lista de mensagens de inconsistência."""
    issues = []
    for i, rec in enumerate(records, start=2):  # row 2 = first data row
        if not rec['cnpj_emitente']:
            issues.append(f"Linha {i}: CNPJ Emitente ausente.")
        if rec['serie_reinf'] == 'S4000' and not _natureza_rendimento_valida(rec['natureza_rendimento']):
            issues.append(
                f"Linha {i}: Natureza Rendimento inválida ({rec['natureza_rendimento']!r}) para S4000 – "
                "deve ser código de 5 dígitos."
            )
        if rec['valor_retido'] <= 0:
            issues.append(f"Linha {i}: Valor Retido deve ser positivo.")
    return issues


# ---------------------------------------------------------------------------
# Construtores XML (portados de fiscal/services/reinf.py)
# ---------------------------------------------------------------------------

def _build_r1000_xml(cnpj: str, razao_social: str, tipo_inscricao: int = 1) -> str:
    """R-1000: Informações do Contribuinte."""
    root = ET.Element('Reinf', xmlns='http://www.reinf.esocial.gov.br/schemas/evtInfoContri/v2_01_01')
    evt = ET.SubElement(root, 'evtInfoContri')
    ide_contrib = ET.SubElement(evt, 'ideContri')
    ET.SubElement(ide_contrib, 'tpInsc').text = str(tipo_inscricao)
    ET.SubElement(ide_contrib, 'nrInsc').text = _digits_only(cnpj)
    ET.SubElement(ide_contrib, 'nmRazao').text = razao_social
    return _prettify(root)


def _build_r2010_xml(cnpj_contribuinte: str, cnpj_prestador: str, records: list[dict],
                     month: int, year: int) -> str:
    """R-2010: Retenção Contribuição Previdenciária – Serviços Tomados (INSS)."""
    root = ET.Element('Reinf', xmlns='http://www.reinf.esocial.gov.br/schemas/evtServTom/v2_01_01')
    evt = ET.SubElement(root, 'evtServTom')

    ide_evento = ET.SubElement(evt, 'ideEvento')
    ET.SubElement(ide_evento, 'indRetif').text = '1'
    ET.SubElement(ide_evento, 'perApur').text = f'{year}-{month:02d}'
    ET.SubElement(ide_evento, 'tpAmb').text = '2'
    ET.SubElement(ide_evento, 'procEmi').text = '1'
    ET.SubElement(ide_evento, 'verProc').text = '1.0'

    ide_contrib = ET.SubElement(evt, 'ideContrib')
    ET.SubElement(ide_contrib, 'tpInsc').text = '1'
    ET.SubElement(ide_contrib, 'nrInsc').text = cnpj_contribuinte

    ide_estab = ET.SubElement(evt, 'ideEstab')
    ET.SubElement(ide_estab, 'tpInsc').text = '1'
    ET.SubElement(ide_estab, 'nrInsc').text = cnpj_contribuinte

    det_evt = ET.SubElement(ide_estab, 'detEvt')

    # Group by NF so each NF gets one <nfSeq> block
    nf_groups: dict[tuple, list[dict]] = defaultdict(list)
    for rec in records:
        key = (rec['numero_nf'], rec['data_emissao'], rec['valor_bruto'])
        nf_groups[key].append(rec)

    for (numero_nf, data_emissao, valor_bruto), nf_records in nf_groups.items():
        nf_seq = ET.SubElement(det_evt, 'nfSeq')
        ET.SubElement(nf_seq, 'nrNF').text = numero_nf
        ET.SubElement(nf_seq, 'dtEmiNF').text = str(data_emissao)
        ET.SubElement(nf_seq, 'vrBruto').text = _fmt_dec(nf_records[0]['valor_bruto'])

        det_ret = ET.SubElement(nf_seq, 'detRet')
        base_total = sum(r['base_calculo'] for r in nf_records)
        retido_total = sum(r['valor_retido'] for r in nf_records)
        ET.SubElement(det_ret, 'vrBaseRet').text = _fmt_dec(base_total)
        ET.SubElement(det_ret, 'vrRet').text = _fmt_dec(retido_total)

    return _prettify(root)


def _build_r4020_xml(cnpj_contribuinte: str, cnpj_prestador: str, records: list[dict],
                     month: int, year: int) -> str:
    """R-4020: Pagamentos/Créditos a Beneficiários PJ (IRRF/CSRF)."""
    root = ET.Element('Reinf', xmlns='http://www.reinf.esocial.gov.br/schemas/evtRetPJ/v2_01_01')
    evt = ET.SubElement(root, 'evtRetPJ')

    ide_evento = ET.SubElement(evt, 'ideEvento')
    ET.SubElement(ide_evento, 'indRetif').text = '1'
    ET.SubElement(ide_evento, 'perApur').text = f'{year}-{month:02d}'
    ET.SubElement(ide_evento, 'tpAmb').text = '2'
    ET.SubElement(ide_evento, 'procEmi').text = '1'
    ET.SubElement(ide_evento, 'verProc').text = '1.0'

    ide_contrib = ET.SubElement(evt, 'ideContrib')
    ET.SubElement(ide_contrib, 'tpInsc').text = '1'
    ET.SubElement(ide_contrib, 'nrInsc').text = cnpj_contribuinte

    ide_pj = ET.SubElement(evt, 'idePJ')
    ET.SubElement(ide_pj, 'cnpjPrestador').text = cnpj_prestador

    # Group by natureza_rendimento
    natureza_groups: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        natureza_groups[rec['natureza_rendimento']].append(rec)

    for natureza, nat_records in natureza_groups.items():
        det_pag = ET.SubElement(ide_pj, 'detPag')
        ET.SubElement(det_pag, 'natRend').text = natureza
        ET.SubElement(det_pag, 'vrBaseRet').text = _fmt_dec(sum(r['base_calculo'] for r in nat_records))
        ET.SubElement(det_pag, 'vrRet').text = _fmt_dec(sum(r['valor_retido'] for r in nat_records))

    return _prettify(root)


def _build_fechamento_xml(evento: str, per_apur: str) -> str:
    """R-2099 / R-4099: Fechamento dos Eventos Periódicos."""
    root = ET.Element('Reinf')
    evt = ET.SubElement(root, evento)
    ide_evento = ET.SubElement(evt, 'ideEvento')
    ET.SubElement(ide_evento, 'perApur').text = per_apur
    return _prettify(root)


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------

def gerar_xmls_reinf(
    xlsx_source,
    cnpj_contribuinte: str,
    razao_social: str,
    month: int,
    year: int,
) -> dict[str, str]:
    """Lê a planilha de controle e retorna os XMLs EFD-Reinf como strings em memória.

    Adequado para uso no browser (PyScript): não escreve arquivos em disco.

    Args:
        xlsx_source:       Planilha de controle (.xlsx) – caminho, bytes ou BytesIO.
        cnpj_contribuinte: CNPJ da empresa declarante (somente dígitos ou formatado).
        razao_social:      Razão social da empresa declarante.
        month:             Mês de apuração (1–12).
        year:              Ano de apuração (ex: 2024).

    Returns:
        Dicionário {nome_arquivo: xml_string} com todos os XMLs gerados.

    Raises:
        ValueError: Se forem encontradas inconsistências nos dados.
    """
    records = read_control_sheet(xlsx_source)
    if not records:
        raise ValueError("Nenhum registro S2000/S4000 encontrado na planilha.")

    issues = validate_records(records)
    if issues:
        raise ValueError("Inconsistências encontradas:\n" + "\n".join(issues))

    cnpj_contribuinte = _digits_only(cnpj_contribuinte)
    per_apur = f'{year}-{month:02d}'

    inss_by_cnpj: dict[str, list[dict]] = defaultdict(list)
    federal_by_cnpj: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        if rec['serie_reinf'] == 'S2000':
            inss_by_cnpj[rec['cnpj_emitente']].append(rec)
        elif rec['serie_reinf'] == 'S4000':
            federal_by_cnpj[rec['cnpj_emitente']].append(rec)

    xmls: dict[str, str] = {}
    xmls['R-1000_Cadastro_Empresa.xml'] = _build_r1000_xml(cnpj_contribuinte, razao_social)

    for cnpj_prestador, recs in inss_by_cnpj.items():
        filename = f'INSS_R2010/R2010_CNPJ_{cnpj_prestador}_{year}{month:02d}.xml'
        xmls[filename] = _build_r2010_xml(cnpj_contribuinte, cnpj_prestador, recs, month, year)

    if inss_by_cnpj:
        xmls['INSS_R2010/R2099_Fechamento.xml'] = _build_fechamento_xml('evtFechaEvPer', per_apur)

    for cnpj_prestador, recs in federal_by_cnpj.items():
        filename = f'Federais_R4020/R4020_CNPJ_{cnpj_prestador}_{year}{month:02d}.xml'
        xmls[filename] = _build_r4020_xml(cnpj_contribuinte, cnpj_prestador, recs, month, year)

    if federal_by_cnpj:
        xmls['Federais_R4020/R4099_Fechamento.xml'] = _build_fechamento_xml('evtFechaEvPer', per_apur)

    return xmls


def gerar_lotes_reinf(
    xlsx_path: str | Path,
    cnpj_contribuinte: str,
    razao_social: str,
    month: int,
    year: int,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Lê a planilha de controle e grava os XMLs EFD-Reinf em disco (uso via CLI).

    Args:
        xlsx_path:        Planilha de controle (.xlsx).
        cnpj_contribuinte: CNPJ da empresa declarante (somente dígitos ou formatado).
        razao_social:     Razão social da empresa declarante.
        month:            Mês de apuração (1–12).
        year:             Ano de apuração (ex: 2024).
        output_dir:       Diretório onde os XMLs serão gravados.

    Returns:
        Dicionário {nome_arquivo: Path} dos arquivos XML gerados.

    Raises:
        ValueError: Se forem encontradas inconsistências nos dados.
    """
    xmls = gerar_xmls_reinf(xlsx_path, cnpj_contribuinte, razao_social, month, year)

    output_dir = Path(output_dir)
    generated: dict[str, Path] = {}

    for filename, xml_str in xmls.items():
        path = output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(xml_str, encoding='utf-8')
        generated[filename] = path

    return generated


__all__ = [
    'read_control_sheet',
    'validate_records',
    'gerar_xmls_reinf',
    'gerar_lotes_reinf',
    '_build_r1000_xml',
    '_build_r2010_xml',
    '_build_r4020_xml',
    '_build_fechamento_xml',
]
