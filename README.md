# AdministrativeToolBox

Utilitários administrativos standalone em Python, inspirados em BS15/djangoproject.
Sem dependência do Django – basta instalar os pacotes em `requirements.txt`.

## Funcionalidades

| Ferramenta | Entrada | Saída |
|---|---|---|
| **SISCAC Payments** | Relatório PDF do SISCAC | CSV com lista de pagamentos |
| **EFD-Reinf XML** | Planilha de controle `.xlsx` | Lotes de arquivos XML EFD-Reinf |

---

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

---

## Uso

### 1. Lista de Pagamentos (CSV) a partir do relatório SISCAC

```bash
python main.py siscac --input relatorio_siscac.pdf --output pagamentos.csv
```

O CSV gerado contém as colunas:
`siscac_pg`, `credor`, `nota_empenho`, `valor_total`, `comprovante`

### 2. Geração de lotes XML EFD-Reinf

```bash
python main.py reinf \
    --input planilha_controle.xlsx \
    --cnpj 12345678000190 \
    --razao "Empresa Exemplo Ltda" \
    --mes 6 \
    --ano 2024 \
    --output-dir saida/
```

Os arquivos são gerados dentro de `saida/`:
```
saida/
├── R-1000_Cadastro_Empresa.xml
├── INSS_R2010/
│   ├── R2010_CNPJ_<cnpj>_202406.xml   (um por CNPJ prestador)
│   └── R2099_Fechamento.xml
└── Federais_R4020/
    ├── R4020_CNPJ_<cnpj>_202406.xml   (um por CNPJ prestador)
    └── R4099_Fechamento.xml
```

Veja `data/README.md` para o formato esperado da planilha de controle.

---

## Testes

```bash
pip install pytest
pytest tests/
```

---

## Estrutura do projeto

```
AdministrativeToolBox/
├── toolbox/
│   ├── __init__.py
│   ├── siscac_payments.py   # Extração SISCAC + geração CSV
│   └── efdreinf_xml.py      # Leitura planilha + geração XML EFD-Reinf
├── data/                    # Arquivos de entrada de exemplo
├── tests/
│   ├── test_siscac.py
│   └── test_efdreinf.py
├── main.py                  # CLI (argparse)
├── requirements.txt
└── README.md
```