"""AdministrativeToolBox - interface desktop simples (Tkinter).

Permite executar duas funcionalidades:
1) Extrair CSV de pagamentos a partir de PDF SISCAC
2) Gerar XMLs EFD-Reinf e salvar em ZIP
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import zipfile

from toolbox.efdreinf_xml import gerar_xmls_reinf
from toolbox.siscac_payments import parse_siscac_report, payments_to_csv_string


class AdministrativeToolBoxApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AdministrativeToolBox")
        self.geometry("760x520")
        self.minsize(700, 500)

        self.mode = tk.StringVar(value="siscac")

        self._build_header()
        self._build_mode_selector()
        self._build_siscac_frame()
        self._build_reinf_frame()
        self._build_actions()
        self._toggle_mode()

    def _build_header(self) -> None:
        title = ttk.Label(
            self,
            text="AdministrativeToolBox",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(pady=(16, 4))

        subtitle = ttk.Label(
            self,
            text="Extraia pagamentos do SISCAC ou gere lotes XML EFD-Reinf",
            font=("Segoe UI", 10),
        )
        subtitle.pack(pady=(0, 12))

    def _build_mode_selector(self) -> None:
        container = ttk.LabelFrame(self, text="Função")
        container.pack(fill="x", padx=16, pady=8)

        ttk.Radiobutton(
            container,
            text="Extrair lista de pagamentos (SISCAC -> CSV)",
            variable=self.mode,
            value="siscac",
            command=self._toggle_mode,
        ).pack(anchor="w", padx=12, pady=6)

        ttk.Radiobutton(
            container,
            text="Gerar XML EFD-Reinf (XLSX/CSV -> ZIP)",
            variable=self.mode,
            value="reinf",
            command=self._toggle_mode,
        ).pack(anchor="w", padx=12, pady=(0, 8))

    def _build_siscac_frame(self) -> None:
        self.siscac_frame = ttk.LabelFrame(self, text="SISCAC")
        self.siscac_frame.pack(fill="x", padx=16, pady=8)

        self.siscac_input = tk.StringVar()
        self.siscac_output = tk.StringVar()

        self._build_file_row(
            self.siscac_frame,
            label="Relatório PDF:",
            variable=self.siscac_input,
            browse_command=self._browse_siscac_input,
        )

        self._build_file_row(
            self.siscac_frame,
            label="Salvar CSV em:",
            variable=self.siscac_output,
            browse_command=self._browse_siscac_output,
        )

    def _build_reinf_frame(self) -> None:
        self.reinf_frame = ttk.LabelFrame(self, text="EFD-Reinf")
        self.reinf_frame.pack(fill="x", padx=16, pady=8)

        self.reinf_input = tk.StringVar()
        self.reinf_output_zip = tk.StringVar()
        self.reinf_cnpj = tk.StringVar()
        self.reinf_razao = tk.StringVar()
        self.reinf_mes = tk.StringVar()
        self.reinf_ano = tk.StringVar()

        self._build_file_row(
            self.reinf_frame,
            label="Planilha/CSV:",
            variable=self.reinf_input,
            browse_command=self._browse_reinf_input,
        )

        self._build_file_row(
            self.reinf_frame,
            label="Salvar ZIP em:",
            variable=self.reinf_output_zip,
            browse_command=self._browse_reinf_output,
        )

        form = ttk.Frame(self.reinf_frame)
        form.pack(fill="x", padx=10, pady=8)

        self._build_labeled_entry(form, "CNPJ contribuinte:", self.reinf_cnpj, 0)
        self._build_labeled_entry(form, "Razão social:", self.reinf_razao, 1)
        self._build_labeled_entry(form, "Mês (1-12):", self.reinf_mes, 2)
        self._build_labeled_entry(form, "Ano (YYYY):", self.reinf_ano, 3)

    def _build_actions(self) -> None:
        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=16, pady=(12, 16))

        run_button = ttk.Button(actions, text="Executar", command=self._run_selected)
        run_button.pack(side="left")

        close_button = ttk.Button(actions, text="Fechar", command=self.destroy)
        close_button.pack(side="right")

    def _build_file_row(
        self,
        parent: ttk.LabelFrame,
        label: str,
        variable: tk.StringVar,
        browse_command,
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=10, pady=6)

        ttk.Label(row, text=label, width=18).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row, text="Selecionar", command=browse_command).pack(side="left")

    def _build_labeled_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label, width=20).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

    def _toggle_mode(self) -> None:
        if self.mode.get() == "siscac":
            self.siscac_frame.pack(fill="x", padx=16, pady=8)
            self.reinf_frame.pack_forget()
        else:
            self.reinf_frame.pack(fill="x", padx=16, pady=8)
            self.siscac_frame.pack_forget()

    def _browse_siscac_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o PDF SISCAC",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.siscac_input.set(path)

    def _browse_siscac_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Salvar CSV",
            defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")],
        )
        if path:
            self.siscac_output.set(path)

    def _browse_reinf_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione planilha de controle ou CSV",
            filetypes=[("Planilhas/CSV", "*.xlsx *.csv"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self.reinf_input.set(path)

    def _browse_reinf_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Salvar ZIP",
            defaultextension=".zip",
            filetypes=[("Arquivo ZIP", "*.zip")],
        )
        if path:
            self.reinf_output_zip.set(path)

    def _run_selected(self) -> None:
        try:
            if self.mode.get() == "siscac":
                self._run_siscac()
            else:
                self._run_reinf()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def _run_siscac(self) -> None:
        input_path = Path(self.siscac_input.get().strip())
        output_path = Path(self.siscac_output.get().strip())

        if not input_path.exists():
            raise ValueError("Selecione um PDF SISCAC válido.")
        if not output_path.parent.exists():
            raise ValueError("Diretório de saída do CSV não existe.")

        payments = parse_siscac_report(input_path)
        csv_text = payments_to_csv_string(payments)
        output_path.write_text(csv_text, encoding="utf-8")

        messagebox.showinfo(
            "Concluído",
            f"CSV gerado com sucesso em:\n{output_path}\n\nRegistros: {len(payments)}",
        )

    def _run_reinf(self) -> None:
        input_path = Path(self.reinf_input.get().strip())
        output_zip = Path(self.reinf_output_zip.get().strip())

        if not input_path.exists():
            raise ValueError("Selecione um arquivo XLSX ou CSV válido.")
        if not output_zip.parent.exists():
            raise ValueError("Diretório de saída do ZIP não existe.")

        cnpj = self.reinf_cnpj.get().strip()
        razao = self.reinf_razao.get().strip()
        mes_texto = self.reinf_mes.get().strip()
        ano_texto = self.reinf_ano.get().strip()

        if not cnpj:
            raise ValueError("Informe o CNPJ do contribuinte.")
        if not razao:
            raise ValueError("Informe a razão social.")

        try:
            mes = int(mes_texto)
            ano = int(ano_texto)
        except ValueError as exc:
            raise ValueError("Mês e ano devem ser numéricos.") from exc

        if mes < 1 or mes > 12:
            raise ValueError("Mês deve estar entre 1 e 12.")
        if ano < 2000 or ano > 2100:
            raise ValueError("Ano inválido.")

        xmls = gerar_xmls_reinf(
            xlsx_source=input_path,
            cnpj_contribuinte=cnpj,
            razao_social=razao,
            month=mes,
            year=ano,
        )

        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for filename, xml_content in xmls.items():
                zf.writestr(filename, xml_content)

        messagebox.showinfo(
            "Concluído",
            f"ZIP gerado com sucesso em:\n{output_zip}\n\nArquivos XML: {len(xmls)}",
        )


def main() -> None:
    app = AdministrativeToolBoxApp()
    app.mainloop()


if __name__ == "__main__":
    main()
