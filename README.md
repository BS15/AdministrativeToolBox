# AdministrativeToolBox

Aplicacao standalone em HTML + JavaScript para uso direto no navegador.

## Escopo atual

Este repositorio foi simplificado para um unico runtime:

- `app.html`
- `vendor/js/xlsx.full.min.js`
- `vendor/js/jszip.min.js`
- `vendor/js/pdf.min.js`
- `vendor/js/pdf.worker.min.js`

Tudo que nao participa desse fluxo foi removido.

## Funcionalidades

| Ferramenta | Entrada | Saida |
|---|---|---|
| SISCAC -> CSV | Relatorio PDF do SISCAC | CSV de pagamentos |
| EFD-Reinf -> ZIP | Planilha `.xlsx` ou `.csv` | ZIP com XMLs |

## Como usar

1. Abra a pasta do projeto.
2. Clique duas vezes em `app.html`.
3. Use a aba desejada e baixe o arquivo gerado.

Sem Python, sem instalacao e sem terminal.

## Distribuicao

Para distribuir a aplicacao, envie:

- `app.html`
- pasta `vendor/js/`