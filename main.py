"""AdministrativeToolBox – CLI entrypoint.

Usage
-----
# Gerar lista de pagamentos (CSV) a partir do relatório SISCAC (PDF)
python main.py siscac --input relatorio.pdf --output pagamentos.csv

# Gerar lotes XML EFD-Reinf a partir da planilha de controle (Excel)
python main.py reinf \\
    --input planilha_controle.xlsx \\
    --cnpj 12345678000190 \\
    --razao "Empresa Exemplo Ltda" \\
    --mes 6 \\
    --ano 2024 \\
    --output-dir saida/
"""

import argparse
import sys
from pathlib import Path


def cmd_siscac(args: argparse.Namespace) -> int:
    """Extrai pagamentos do PDF SISCAC e gera CSV."""
    from toolbox.siscac_payments import generate_payments_csv

    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"Erro: arquivo não encontrado: {pdf_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    try:
        result = generate_payments_csv(pdf_path, output_path)
        print(f"CSV gerado com sucesso: {result}")
        return 0
    except Exception as exc:
        print(f"Erro ao processar relatório SISCAC: {exc}", file=sys.stderr)
        return 1


def cmd_reinf(args: argparse.Namespace) -> int:
    """Lê planilha de controle e gera arquivos XML EFD-Reinf."""
    from toolbox.efdreinf_xml import gerar_lotes_reinf

    xlsx_path = Path(args.input)
    if not xlsx_path.exists():
        print(f"Erro: arquivo não encontrado: {xlsx_path}", file=sys.stderr)
        return 1

    try:
        generated = gerar_lotes_reinf(
            xlsx_path=xlsx_path,
            cnpj_contribuinte=args.cnpj,
            razao_social=args.razao,
            month=args.mes,
            year=args.ano,
            output_dir=args.output_dir,
        )
        print(f"{len(generated)} arquivo(s) XML gerado(s) em '{args.output_dir}':")
        for name in generated:
            print(f"  {name}")
        return 0
    except ValueError as exc:
        print(f"Erro de validação: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erro ao gerar XMLs EFD-Reinf: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='python main.py',
        description='AdministrativeToolBox – utilitários administrativos standalone',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # siscac sub-command
    p_siscac = sub.add_parser('siscac', help='Gerar lista de pagamentos CSV a partir do relatório SISCAC')
    p_siscac.add_argument('--input', '-i', required=True, metavar='PDF', help='Caminho do relatório SISCAC (PDF)')
    p_siscac.add_argument('--output', '-o', required=True, metavar='CSV', help='Caminho do arquivo CSV de saída')

    # reinf sub-command
    p_reinf = sub.add_parser('reinf', help='Gerar lotes XML EFD-Reinf a partir da planilha de controle')
    p_reinf.add_argument('--input', '-i', required=True, metavar='XLSX',
                         help='Planilha de controle (.xlsx)')
    p_reinf.add_argument('--cnpj', required=True, metavar='CNPJ',
                         help='CNPJ do contribuinte declarante (somente dígitos ou formatado)')
    p_reinf.add_argument('--razao', required=True, metavar='RAZAO_SOCIAL',
                         help='Razão social do contribuinte declarante')
    p_reinf.add_argument('--mes', '-m', required=True, type=int, metavar='MES',
                         help='Mês de apuração (1–12)')
    p_reinf.add_argument('--ano', '-a', required=True, type=int, metavar='ANO',
                         help='Ano de apuração (ex: 2024)')
    p_reinf.add_argument('--output-dir', '-o', required=True, metavar='DIR',
                         help='Diretório de saída para os arquivos XML')

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == 'siscac':
        return cmd_siscac(args)
    if args.command == 'reinf':
        return cmd_reinf(args)

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
