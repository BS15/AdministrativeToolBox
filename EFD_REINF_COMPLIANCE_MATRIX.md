# EFD-Reinf Compliance Matrix (Phase Baseline)

This file tracks the current browser generator implementation versus uploaded EFD-Reinf layout artifacts.

## Source Artifacts

- EFD REINF DOCUMENTATION/R-1000-NT 02_2025-v2_01_02f/R-1000-evtInfoContribuinte-v2_01_02f.xsd
- EFD REINF DOCUMENTATION/XSD EFD-Reinf v2.1.2d/20240930/R-2010-evtTomadorServicos-v2_01_02d.xsd
- EFD REINF DOCUMENTATION/R-4010 e R-4020-NT 01_2025-v2_01_02e/R-4010-evt4010PagtoBeneficiarioPF-v2_01_02e.xsd
- EFD REINF DOCUMENTATION/R-4010 e R-4020-NT 01_2025-v2_01_02e/R-4020-evt4020PagtoBeneficiarioPJ-v2_01_02e.xsd
- EFD REINF DOCUMENTATION/XSD EFD-Reinf v2.1.2d/20240930/R-2099-evtFechamento-v2_01_02d.xsd
- EFD REINF DOCUMENTATION/XSD EFD-Reinf v2.1.2d/20240930/R-4099-evt4099FechamentoDirf-v2_01_02d.xsd

## Current Status

| Event | Current Namespace/Shape | Target Layout | Status |
|---|---|---|---|
| R-1000 | v2_01_02 namespace + ideEvento/infoContri skeleton | v2_01_02 full required field semantics | Partially migrated |
| R-2010 | v2_01_02 namespace + infoServTom/ideEstabObra/idePrestServ/nfs/infoTpServ | v2_01_02 infoServTom/ideEstabObra hierarchy | Structurally migrated (partial semantics pending) |
| R-4010 | v2_01_02 namespace + ideEstab/ideBenef/idePgto/infoPgto (PF) | v2_01_02 evtRetPF hierarchy | Structurally migrated (partial semantics pending) |
| R-4020 | v2_01_02 namespace + ideEstab/ideBenef/idePgto/infoPgto/retencoes | v2_01_02 ideEstab/ideBenef/idePgto/infoPgto hierarchy | Structurally migrated (partial semantics pending) |
| R-2099 | dedicated builder with v2_01_02 namespace + full required infoFech flags | v2_01_02 evtFechaEvPer full conformance | Structurally migrated |
| R-4099 | dedicated builder with v2_01_02 namespace + ideContri/infoFech | v2_01_02 evtFech full conformance | Partially migrated |

## Phase 1-4 Implemented

- Added EFD-Reinf XLSX template download in UI (template_efd_reinf.xlsx).
- Added stricter header validation for uploaded XLSX/CSV.
- Added Excel serial date parsing support.
- Added upload data-contract guardrails to reduce malformed sheet ingestion.
- Migrated key namespaces from v2_01_01 to v2_01_02 families for implemented events.
- Replaced generic fechamento output for R-2099 and R-4099 with dedicated builders.
- Added S4000 split by beneficiary type (PF -> R-4010, PJ -> R-4020).
- Added mandatory R-2099 closure flags required by XSD (evtServTm/evtServPr/evtAssDespRec/evtAssDespRep/evtComProd/evtCPRB/evtAquis).

## Next Implementation Phases

1. Add local XSD validation pipeline before ZIP download.
2. Add XMLDSig signature support for generated events.
3. Implement envio de lote via webservice Receita (SOAP + mTLS) and protocol lifecycle.
4. Refine semantic mapping for optional blocks (natJur, processos, blocos complementares de retencao/isencao).
