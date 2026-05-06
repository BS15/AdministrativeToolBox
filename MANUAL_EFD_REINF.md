# Manual do Usuario - EFD-Reinf (AdministrativeToolBox)

Este manual explica como usar a funcionalidade **EFD-Reinf -> ZIP de XMLs** da aplicacao para separar corretamente informacoes de **INSS (serie S2000)** e **Impostos Federais (serie S4000)**, gerar os XMLs e entender cada coluna do template.

## 1. O que esta funcionalidade faz

A aba EFD-Reinf:

1. Le uma planilha `.xlsx` ou `.csv`.
2. Interpreta os registros por linha.
3. Separa os dados por serie:
- `S2000` -> grupo INSS (evento R-2010)
- `S4000` -> grupo Federais (evento R-4020)
4. Gera XMLs por prestador/beneficiario e eventos de fechamento.
5. Compacta tudo em um ZIP para download.

## 2. O que voce precisa antes de comecar

1. Arquivo de controle `.xlsx` ou `.csv` com cabecalho reconhecivel.
2. CNPJ do contribuinte (somente numeros).
3. Razao social do contribuinte.
4. Mes e ano de apuracao.

## 3. Passo a passo rapido

1. Abra `app.html` no navegador.
2. Acesse a aba **EFD-Reinf -> ZIP de XMLs**.
3. Clique em **Baixar Template XLSX EFD-Reinf** (recomendado para evitar erro de cabecalho).
4. Preencha a planilha (ver glossario na secao 8).
5. Selecione o arquivo no campo de upload.
6. Informe CNPJ, razao social, mes e ano.
7. Clique em **Gerar ZIP de XMLs**.
8. Baixe o arquivo `EFD_Reinf_AAAAMM.zip`.

## 4. Como informar INSS (S2000)

Use serie `S2000` para registros de INSS no fluxo do evento R-2010.

### 4.1 Regras praticas

1. Preencha `serie_reinf` com `S2000` na linha.
2. Informe pelo menos:
- `cnpj_emitente`
- `numero_nf`
- `data_emissao`
- e algum valor monetario relevante
3. Para linha tributada, `valor_retido` deve ser maior que zero.

### 4.2 O que o sistema gera

1. Um XML R-2010 por CNPJ emitente em:
- `INSS_R2010/R2010_CNPJ_<cnpj>_<aaaamm>.xml`
2. Se houver qualquer linha S2000 no periodo, gera tambem:
- `INSS_R2010/R2099_Fechamento.xml`

## 5. Como informar Impostos Federais (S4000)

Use serie `S4000` para registros de impostos federais no fluxo do evento R-4020.

### 5.1 Regras praticas

1. Preencha `serie_reinf` com `S4000` na linha.
2. Informe `natureza_rendimento` com 5 digitos (ex.: `15001`).
3. Para linha tributada, informe `base_calculo` e/ou `valor_retido`.
4. Para rendimento isento/imune, marque `is_rendimento_isento` e informe valor em `valor_bruto` ou `base_calculo`.

### 5.2 O que o sistema gera

1. Um XML R-4020 por CNPJ emitente em:
- `Federais_R4020/R4020_CNPJ_<cnpj>_<aaaamm>.xml`
2. Se houver qualquer linha S4000 no periodo, gera tambem:
- `Federais_R4020/R4099_Fechamento.xml`

## 6. Regras automáticas importantes da aplicacao

1. Se `serie_reinf` nao existir no cabecalho, o sistema tenta inferir:
- natureza valida (5 digitos) -> tende para S4000
- sem natureza valida -> tende para S2000
2. Se houver `tp_isencao` ou `desc_isencao`, a linha passa a ser tratada como rendimento isento.
3. Datas aceitas:
- `DD/MM/AAAA`
- `AAAA-MM-DD`
- serial de data do Excel
4. Decimais aceitos:
- `1234,56`
- `1.234,56`
- `1234.56`

## 7. Estrutura esperada do ZIP gerado

Exemplo de saida:

1. `R-1000_Cadastro_Empresa.xml`
2. `INSS_R2010/R2010_CNPJ_XXXXXXXXXXXXXX_AAAAMM.xml` (1..N)
3. `INSS_R2010/R2099_Fechamento.xml` (quando houver S2000)
4. `Federais_R4020/R4020_CNPJ_XXXXXXXXXXXXXX_AAAAMM.xml` (1..N)
5. `Federais_R4020/R4099_Fechamento.xml` (quando houver S4000)

## 8. Glossario das colunas do template EFD-Reinf

### 8.1 Colunas principais

Na coluna "Obrigatoriedade por serie/evento", o texto distingue:

1. o que e obrigatorio no layout/XML do evento;
2. o que e obrigatorio para uso desta ferramenta/template.

| Coluna | Obrigatoriedade por serie/evento | Uso | Exemplo |
|---|---|---|---|
| `cnpj_emitente` | S2000: obrigatorio na ferramenta. S4000: obrigatorio na ferramenta. | CNPJ do emitente/prestador relacionado a linha. Somente numeros. | `12345678000199` |
| `nome_emitente` | S2000: opcional. S4000: opcional. | Nome do emitente para referencia e apoio. | `PRESTADOR EXEMPLO LTDA` |
| `numero_nf` | S2000: obrigatorio na ferramenta e no agrupamento do processamento. S4000: obrigatorio na ferramenta para identificar a linha/documento, embora nao seja campo do XML R-4010/R-4020. | Numero da nota/documento da linha. | `12345` |
| `serie_nf` | S2000: obrigatorio no XML R-2010; se vazio, a ferramenta preenche `1`. S4000: nao aplicavel ao XML; opcional na ferramenta. | Serie da NF. Se vazio, o sistema usa padrao na montagem do XML S2000. | `1` |
| `tp_servico` | S2000: obrigatorio. S4000: nao aplicavel. | Codigo do tipo de servico (9 digitos), usado no fluxo de servicos tomados (S2000/R-2010). | `000000001` |
| `data_emissao` | S2000: obrigatoria e usada em `dtEmissaoNF`. S4000: opcional se `data_pagamento` for informada; pode ser usada como fallback de compatibilidade para `dtFG`. | Data da nota/documento. | `2026-01-15` |
| `data_pagamento` | S2000: nao aplicavel. S4000: obrigatoria no conceito do evento (`dtFG`); na ferramenta, pode ser suprida por `data_emissao` como fallback. | Data do pagamento para `dtFG` (R-4010/R-4020). | `2026-01-20` |
| `valor_bruto` | S2000: obrigatorio no XML R-2010. S4000: opcional, mas recomendado quando houver pagamento bruto ou linha isenta/imune. | Valor bruto da operacao. Pode ser usado como fallback de base/isencao. | `1000,00` |
| `base_ir` | S2000: nao aplicavel. S4000: opcional no XML; usar quando houver base individual de IR. | Base do IR individual (mapeia para `vlrBaseIR` no R-4020). | `1000,00` |
| `base_calculo` | S2000: obrigatoria para compor `vlrBaseRet`. S4000: alias opcional aceito para `base_ir`. | Base de calculo usada pela ferramenta; em S4000 funciona como alias de `base_ir`. | `1000,00` |
| `base_agreg` | S2000: nao aplicavel. S4000: opcional. | Base das retencoes agregadas (quando houver tributacao agregada). | `1000,00` |
| `base_csll` | S2000: nao aplicavel. S4000: opcional. | Base de calculo da CSLL. | `1000,00` |
| `base_cofins` | S2000: nao aplicavel. S4000: opcional. | Base de calculo da Cofins. | `1000,00` |
| `base_pis` | S2000: nao aplicavel. S4000: opcional. | Base de calculo do PIS/Pasep. | `1000,00` |
| `valor_ret_ir` | S2000: nao aplicavel diretamente. S4000: condicional; em linha tributada, deve haver ao menos uma retencao informada (IR, agregada, CSLL, Cofins ou PIS). | Valor do IR retido individual (mapeia para `vlrIR` no R-4020). Em linha tributada deve ser positivo. | `15,00` |
| `valor_retido` | S2000: obrigatorio para compor `vlrRetencao`. S4000: alias condicional aceito para `valor_ret_ir`. | Campo de retencao usado pela ferramenta; em S4000 funciona como alias de `valor_ret_ir`. | `15,00` |
| `valor_ret_agreg` | S2000: nao aplicavel. S4000: opcional; pode suprir a exigencia de haver retencao em linha tributada. | Valor retido em formato agregado (sem detalhamento por tributo). | `15,00` |
| `valor_ret_csll` | S2000: nao aplicavel. S4000: opcional; pode suprir a exigencia de haver retencao em linha tributada. | Valor retido de CSLL. | `5,00` |
| `valor_ret_cofins` | S2000: nao aplicavel. S4000: opcional; pode suprir a exigencia de haver retencao em linha tributada. | Valor retido de Cofins. | `6,00` |
| `valor_ret_pis` | S2000: nao aplicavel. S4000: opcional; pode suprir a exigencia de haver retencao em linha tributada. | Valor retido de PIS/Pasep. | `4,00` |
| `codigo_imposto` | S2000: opcional. S4000: opcional. | Codigo de imposto/receita utilizado no controle. | `5952` |
| `serie_reinf` | S2000/S4000: recomendada. Se ausente, a ferramenta tenta inferir; para reduzir ambiguidade, preencha explicitamente. | Define fluxo: `S2000` (INSS) ou `S4000` (Federais). | `S4000` |
| `natureza_rendimento` | S2000: nao aplicavel. S4000: obrigatoria no XML e na ferramenta. | Natureza de rendimento com 5 digitos. | `15001` |
| `is_rendimento_isento` | S2000: nao aplicavel. S4000: condicional; usar quando a linha for isenta/imune. | Marque quando a linha for isenta/imune. Aceita `true`, `1`, `sim`, `x`, etc. | `false` |
| `tp_isencao` | S2000: nao aplicavel. S4000: condicional; usar quando houver tratamento de isencao/imunidade que deva ser classificado. | Tipo de isencao usado no tratamento de linha isenta/imune. | `99` |
| `desc_isencao` | S2000: nao aplicavel. S4000: opcional; ajuda a qualificar a isencao/imunidade e influencia a inferencia de `isenImun`. | Descricao da isencao/imunidade para apoio e classificacao. | `Imunidade constitucional` |
| `cnpj_beneficiario` | S2000: nao aplicavel. S4000: opcional no estado atual da ferramenta; se vazio, ela usa `cnpj_emitente` para identificar o beneficiario PJ. | CNPJ do beneficiario informado na linha. | `00987654000177` |
| `nome_beneficiario` | S2000: nao aplicavel. S4000: opcional. | Nome do beneficiario para apoio e montagem de campos de saida. | `BENEFICIARIO EXEMPLO SA` |
| `tipo_beneficiario` | S2000: nao aplicavel. S4000: opcional no estado atual da ferramenta; mantido para compatibilidade e futura separacao PF/PJ. | Tipo do beneficiario (`PJ` padrao quando vazio). | `PJ` |

### 8.2 Como preencher por tipo de linha

#### Linha INSS (S2000)

1. `serie_reinf = S2000`
2. Preencher dados de NF e retencao (`valor_retido > 0`)
3. `data_emissao` e utilizada como `dtEmissaoNF` no R-2010
4. `natureza_rendimento` nao e foco principal desse fluxo

#### Linha Federais tributada (S4000)

1. `serie_reinf = S4000`
2. `natureza_rendimento` com 5 digitos
3. Informar `data_pagamento` (usa `data_emissao` como fallback)
4. `base_ir` e/ou `valor_ret_ir` (tambem aceita aliases `base_calculo`/`valor_retido`)

#### Linha Federais isenta/imune (S4000)

1. `serie_reinf = S4000`
2. `is_rendimento_isento = true` (ou equivalente)
3. informar valor em `valor_bruto` e/ou `base_calculo`
4. opcional: `tp_isencao` e `desc_isencao`

## 9. Erros comuns e como corrigir

### 9.1 "Cabecalho incompleto"

Causa: faltam colunas minimas reconhecidas.

Como corrigir:

1. Use o template baixado pela propria tela.
2. Garanta no minimo: `cnpj_emitente`, `numero_nf`, `data_emissao` ou `data_pagamento`, e alguma coluna de valor (`valor_ret_ir`/`valor_retido`, `base_ir`/`base_calculo` ou `valor_bruto`).

### 9.2 "Natureza Rendimento invalida para S4000"

Causa: `natureza_rendimento` nao tem 5 digitos em linha `S4000`.

Como corrigir:

1. Ajuste para padrao numerico de 5 digitos (ex.: `15001`).

### 9.3 "Valor Retido deve ser positivo"

Causa: linha tributada sem valor retido.

Como corrigir:

1. Informe `valor_retido` > 0.
2. Se a linha for isenta/imune, marque `is_rendimento_isento` e informe valor bruto/base.

### 9.4 "Rendimento isento deve estar na serie S4000"

Causa: linha marcada como isenta em serie diferente.

Como corrigir:

1. Troque `serie_reinf` para `S4000` na linha isenta/imune.

## 10. Boas praticas operacionais

1. Sempre iniciar pelo template oficial da tela.
2. Manter uma linha por documento/ocorrencia de retencao.
3. Evitar caracteres especiais desnecessarios nos campos textuais.
4. Validar um lote pequeno antes de processar o mes inteiro.
5. Arquivar o ZIP gerado junto da planilha de origem para rastreabilidade.

## 11. Limite funcional atual

A ferramenta gera os XMLs em lote no navegador para apoio operacional. A transmissao, assinatura digital e protocolo nos ambientes oficiais devem seguir o processo institucional adotado pela sua equipe fiscal.
