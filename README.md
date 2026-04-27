# AdministrativeToolBox

Utilitarios administrativos com modo standalone em HTML + JavaScript.
Pode ser usado direto no navegador, sem instalacao e sem terminal.

## Funcionalidades

| Ferramenta | Entrada | Saída |
|---|---|---|
| **SISCAC Payments** | Relatório PDF do SISCAC | CSV com lista de pagamentos |
| **EFD-Reinf XML** | Planilha de controle `.xlsx` ou `.csv` | Lotes de arquivos XML EFD-Reinf |

---

## Uso Mais Simples (Sem Instalar Nada)

Abra `app.html` no navegador.

Pronto: sem Python, sem dependencias e sem linha de comando.

---

## Uso

### Interface no navegador (HTML + JavaScript) - recomendado

Arquivo de entrada:
- `app.html`

Dependencias locais ja inclusas no repositorio:
- `vendor/js/xlsx.full.min.js`
- `vendor/js/jszip.min.js`
- `vendor/js/pdf.min.js`

Esse fluxo foi feito para rodar diretamente por `file://` ao abrir o HTML.

### Interface no navegador (PyScript) - alternativa legada

A pasta `web/` foi mantida para compatibilidade historica.
Para uso final sem instalacao e sem terminal, prefira sempre `app.html`.

### Interface gráfica simples (desktop)

Execute a interface para escolher a funcionalidade, selecionar arquivos de entrada e gerar saídas:

```bash
python desktop_app.py
```

Fluxos disponíveis na interface:
- **SISCAC -> CSV**: seleciona PDF e caminho do CSV de saída.
- **EFD-Reinf -> ZIP**: seleciona XLSX/CSV, informa CNPJ/razão social/mês/ano e gera um ZIP com todos os XMLs.

### 1. Lista de Pagamentos (CSV) a partir do relatório SISCAC

```bash
python main.py siscac --input relatorio_siscac.pdf --output pagamentos.csv
```

O CSV gerado contém as colunas:
`credor`, `siscac_pg`, `valor_total`, `data_contabilizado`, `comprovante`

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

Também é aceito CSV com o schema:
`CNPJ`, `Abreviatura`, `Data pagto`, `Natureza rendimento (cód. Ecac)`,
`Cód. Receita (siscac)`, `Valor tributável`, `Retenção agregada`, `Retenção individual`.

---

## Testes

```bash
pip install pytest
pytest tests/
```

---

## Deploy e distribuição para usuários finais

### Distribuição browser-first (sem EXE)

Distribua o projeto com o arquivo `app.html` e a pasta `vendor/js/`.
O usuario final so precisa abrir `app.html` no navegador.

### Opção A: rodar como aplicação Python

1. Instale Python 3.11+ no computador do usuário.
2. Instale dependências:

```bash
pip install -r requirements.txt
```

3. Inicie a aplicação:

```bash
python desktop_app.py
```

### Opção B: gerar executável (PyInstaller)

Essa opção gera um arquivo executável para distribuição.

1. Instale PyInstaller no ambiente de build:

```bash
pip install pyinstaller
```

2. Gere o executável:

```bash
pyinstaller --onefile --noconsole --name AdministrativeToolBox desktop_app.py
```

3. Distribua o arquivo em `dist/AdministrativeToolBox` (ou `AdministrativeToolBox.exe` no Windows).

> Recomenda-se gerar o executável no mesmo sistema operacional de destino (Windows para Windows, Linux para Linux, etc.).

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
├── desktop_app.py           # Interface desktop (Tkinter)
├── main.py                  # CLI (argparse)
├── requirements.txt
└── README.md
```