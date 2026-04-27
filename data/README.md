# Planilha/CSV de Controle EFD-Reinf – Formato Esperado

Coloque seu arquivo `.xlsx` ou `.csv` aqui para usar com o comando `reinf`.

## Colunas obrigatórias

| Coluna                | Descrição                                                  |
|-----------------------|------------------------------------------------------------|
| CNPJ Emitente         | CNPJ do prestador de serviço (dígitos ou formatado)        |
| Nome Emitente         | Razão social do prestador                                  |
| Número NF             | Número da nota fiscal                                      |
| Série NF              | Série da nota fiscal (opcional)                            |
| Data Emissão          | Data de emissão (DD/MM/AAAA ou AAAA-MM-DD)                 |
| Valor Bruto           | Valor bruto da NF (numérico)                               |
| Código Imposto        | Código de receita / imposto                                |
| Série Reinf           | `S2000` (INSS) ou `S4000` (Federal IRRF/CSRF)              |
| Natureza Rendimento   | Código de 5 dígitos – **obrigatório para S4000**           |
| Base de Cálculo       | Base de cálculo / rendimento tributável                    |
| Valor Retido          | Valor do imposto retido                                    |
| CNPJ Beneficiário     | CNPJ/CPF do beneficiário (usado em S4000)                  |
| Nome Beneficiário     | Nome do beneficiário (usado em S4000)                      |
| Tipo Beneficiário     | `PF` ou `PJ`                                               |

Linhas onde a coluna **Série Reinf** não for `S2000` ou `S4000` são ignoradas.

## Schema CSV suportado

O gerador também aceita CSV com as colunas:

| Coluna                               | Mapeamento interno |
|--------------------------------------|--------------------|
| CNPJ                                 | CNPJ Emitente |
| Abreviatura                          | Nome Emitente |
| Data pagto                           | Data Emissão |
| Natureza rendimento (cód. Ecac)      | Natureza Rendimento |
| Cód. Receita (siscac)                | Código Imposto |
| Valor tributável                     | Base de Cálculo / Valor Bruto |
| Retenção agregada                    | Valor Retido (fallback) |
| Retenção individual                  | Valor Retido |

Quando o CSV não possui a coluna `Série Reinf`, a série é inferida:
- `S4000` se a Natureza de Rendimento for um código válido de 5 dígitos.
- `S2000` nos demais casos.
