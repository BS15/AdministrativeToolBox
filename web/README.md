# Interface Browser (PyScript) - Offline

Esta pasta contém a interface web para rodar o AdministrativeToolBox no navegador.
O projeto está configurado para usar assets locais (self-host), sem depender de CDN em runtime.

## Preparar assets offline

Execute uma vez em ambiente com internet para baixar os artefatos:

```bash
./web/setup_offline_assets.sh
```

Isso preenche:
- `web/vendor/pyscript/`
- `web/vendor/pyodide/`
- `web/vendor/wheels/`

O script baixa os chunks dependentes do runtime PyScript automaticamente,
evitando erro de importação de módulos JavaScript em ambiente sem internet.

## Como usar

1. Inicie um servidor HTTP na raiz do projeto:

```bash
python -m http.server 8000
```

2. Abra no navegador:

```text
http://localhost:8000/web/
```

## Funcionalidades

- SISCAC -> CSV: envia PDF e baixa CSV.
- EFD-Reinf -> ZIP: envia XLSX/CSV e baixa ZIP com XMLs.

## Arquivos

- `index.html`: interface e layout.
- `app.py`: lógica PyScript de upload/processamento/download.
- `pyscript.toml`: configuração de pacotes e fetch dos módulos do projeto.
- `setup_offline_assets.sh`: baixa e prepara os assets offline.
