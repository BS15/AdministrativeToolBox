# AdministrativeToolBox

Aplicacao standalone em HTML + JavaScript para uso direto no navegador.

## Escopo atual

Este repositorio roda 100% no navegador. As entradas HTML ficam na raiz do projeto e apenas as bibliotecas JavaScript permanecem em pasta.

- `app.html` - launcher com todas as ferramentas
- `payments-report-extraction.html` - entrada standalone de Extração de Pagamentos
- `efd-reinf.html` - entrada standalone de EFD-Reinf
- `diarias.html` - entrada standalone de Diarias
- `vendor/js/xlsx.full.min.js`
- `vendor/js/jszip.min.js`
- `vendor/js/pdf.min.js`
- `vendor/js/pdf.worker.min.js`

## Funcionalidades

| Ferramenta | Entrada | Saida |
|---|---|---|
| SISCAC -> CSV | Relatorio PDF do SISCAC | CSV de pagamentos |
| EFD-Reinf -> ZIP | Planilha `.xlsx` ou `.csv` | ZIP com XMLs |
| Diarias Lote -> SCD PDF | CSV de diarias | ZIP com PDFs SCD |
| Diaria Individual -> SCD PDF | Formulario web | PDF SCD |

## Como usar

1. Abra a pasta do projeto.
2. Escolha uma das entradas abaixo:
	- `app.html` para abrir todas as ferramentas no launcher principal.
	- `payments-report-extraction.html` para abrir somente Extração de Pagamentos.
	- `efd-reinf.html` para abrir somente EFD-Reinf.
	- `diarias.html` para abrir somente Diarias.
3. Use a ferramenta e baixe o arquivo gerado.

As entradas standalone carregam o `app.html` com a ferramenta correspondente ja selecionada em modo dedicado.

Sem Python, sem instalacao e sem terminal.

## Estrutura de arquivos

- Os arquivos HTML de entrada ficam na raiz do projeto.
- Apenas a pasta `vendor/js/` precisa acompanhar a distribuicao para funcionamento offline.
- Nao ha dependencia de servidor local, build ou instalacao de pacotes.

## Distribuicao

Para distribuir a aplicacao, envie:

- `app.html`
- `payments-report-extraction.html`
- `efd-reinf.html`
- `diarias.html`
- pasta `vendor/js/`

Nao e necessario distribuir pasta `apps/`.

## Manual EFD-Reinf

- Consulte o manual completo em `MANUAL_EFD_REINF.md`.