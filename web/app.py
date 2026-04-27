from __future__ import annotations

import base64
import io
import zipfile

from js import Uint8Array
from pyscript import document, when

from toolbox.efdreinf_xml import gerar_xmls_reinf
from toolbox.siscac_payments import parse_siscac_report, payments_to_csv_string


def status(msg: str) -> None:
    document.querySelector("#status").textContent = msg


def set_mode(mode: str) -> None:
    siscac_section = document.querySelector("#siscac-section")
    reinf_section = document.querySelector("#reinf-section")
    if mode == "siscac":
        siscac_section.classList.remove("hidden")
        reinf_section.classList.add("hidden")
    else:
        reinf_section.classList.remove("hidden")
        siscac_section.classList.add("hidden")


async def file_to_bytes(input_selector: str) -> bytes:
    input_el = document.querySelector(input_selector)
    files = input_el.files
    if not files or files.length == 0:
        raise ValueError("Selecione um arquivo antes de executar.")

    file_obj = files.item(0)
    arr_buf = await file_obj.arrayBuffer()
    js_bytes = Uint8Array.new(arr_buf)
    return bytes(js_bytes.to_py())


def trigger_download(filename: str, payload: bytes, mime: str) -> None:
    b64 = base64.b64encode(payload).decode("ascii")
    href = f"data:{mime};base64,{b64}"

    anchor = document.createElement("a")
    anchor.href = href
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()


@when("change", "#mode")
def on_mode_change(event) -> None:
    set_mode(event.target.value)


@when("click", "#run-siscac")
async def on_run_siscac(event) -> None:
    try:
        status("Lendo PDF SISCAC...")
        pdf_bytes = await file_to_bytes("#siscac-file")
        payments = parse_siscac_report(pdf_bytes)
        csv_text = payments_to_csv_string(payments)

        filename = document.querySelector("#siscac-filename").value.strip() or "pagamentos.csv"
        if not filename.lower().endswith(".csv"):
            filename += ".csv"

        trigger_download(filename, csv_text.encode("utf-8"), "text/csv;charset=utf-8")
        status(f"Concluído: {len(payments)} registro(s) processado(s).")
    except Exception as exc:
        status(f"Erro no SISCAC: {exc}")


@when("click", "#run-reinf")
async def on_run_reinf(event) -> None:
    try:
        status("Lendo arquivo de controle e gerando XMLs...")
        source_bytes = await file_to_bytes("#reinf-file")

        cnpj = document.querySelector("#reinf-cnpj").value.strip()
        razao = document.querySelector("#reinf-razao").value.strip()
        mes_text = document.querySelector("#reinf-mes").value.strip()
        ano_text = document.querySelector("#reinf-ano").value.strip()
        filename = document.querySelector("#reinf-filename").value.strip() or "efdreinf_xmls.zip"

        if not cnpj:
            raise ValueError("Informe o CNPJ do contribuinte.")
        if not razao:
            raise ValueError("Informe a razão social.")

        month = int(mes_text)
        year = int(ano_text)
        if month < 1 or month > 12:
            raise ValueError("Mês deve estar entre 1 e 12.")

        xmls = gerar_xmls_reinf(
            xlsx_source=source_bytes,
            cnpj_contribuinte=cnpj,
            razao_social=razao,
            month=month,
            year=year,
        )

        if not filename.lower().endswith(".zip"):
            filename += ".zip"

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path, content in xmls.items():
                zf.writestr(path, content)

        trigger_download(filename, zip_buf.getvalue(), "application/zip")
        status(f"Concluído: {len(xmls)} XML(s) gerado(s).")
    except Exception as exc:
        status(f"Erro no EFD-Reinf: {exc}")


set_mode("siscac")
status("Pronto para uso.")
