#!/usr/bin/env python3
"""
Extrai vencimentos de ASO do portal eSocial e exporta em JSON/CSV.

Observação: o login no eSocial pode exigir certificado digital/2FA.
Por isso, o script abre o navegador e aguarda confirmação manual do usuário.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class AsoRecord:
    cpf: str = ""
    nome: str = ""
    re: str = ""
    vencimento_aso: str = ""
    status: str = ""
    origem: str = "eSocial"


def parse_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def normalize_date(value: str) -> str:
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else ""


def looks_like_header(row: list[str]) -> bool:
    content = " ".join(x.lower() for x in row)
    return "cpf" in content or "venc" in content or "aso" in content


def scrape_table_rows(driver: webdriver.Chrome) -> list[AsoRecord]:
    rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
    if not rows:
        return []

    headers: list[str] = []
    records: list[AsoRecord] = []
    for row in rows:
        cols = [c.text.strip() for c in row.find_elements(By.CSS_SELECTOR, "th,td")]
        cols = [c for c in cols if c]
        if not cols:
            continue
        if not headers and looks_like_header(cols):
            headers = [c.lower() for c in cols]
            continue
        if headers:
            row_map = {headers[i]: cols[i] for i in range(min(len(headers), len(cols)))}
            rec = AsoRecord(
                cpf=row_map.get("cpf", ""),
                nome=row_map.get("nome", ""),
                re=row_map.get("re", row_map.get("matrícula", row_map.get("matricula", ""))),
                vencimento_aso=normalize_date(
                    row_map.get("vencimento aso", row_map.get("vencimento", row_map.get("aso", "")))
                ),
                status=row_map.get("status", ""),
            )
        else:
            rec = AsoRecord(
                cpf=cols[0] if len(cols) > 0 else "",
                nome=cols[1] if len(cols) > 1 else "",
                re=cols[2] if len(cols) > 2 else "",
                vencimento_aso=normalize_date(cols[3] if len(cols) > 3 else ""),
                status=cols[4] if len(cols) > 4 else "",
            )
        records.append(rec)

    return [r for r in records if r.nome and r.vencimento_aso]


def filter_due(records: Iterable[AsoRecord], due_days: int | None) -> list[AsoRecord]:
    if due_days is None:
        return list(records)
    limit = date.today() + timedelta(days=due_days)
    result = []
    for rec in records:
        dt = parse_date(rec.vencimento_aso)
        if dt and dt <= limit:
            result.append(rec)
    return result


def write_json(records: list[AsoRecord], path: Path) -> None:
    path.write_text(
        json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(records: list[AsoRecord], path: Path) -> None:
    fields = ["cpf", "nome", "re", "vencimento_aso", "status", "origem"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))


def build_driver(headless: bool) -> webdriver.Chrome:
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extrai vencimentos de ASO do eSocial")
    parser.add_argument("--login-url", default="https://www.esocial.gov.br/", help="URL inicial para login")
    parser.add_argument("--aso-url", default="", help="URL da tela/listagem de ASO após login")
    parser.add_argument("--output-json", default="aso_esocial.json", help="Arquivo JSON de saída")
    parser.add_argument("--output-csv", default="aso_esocial.csv", help="Arquivo CSV de saída")
    parser.add_argument("--due-days", type=int, default=60, help="Filtrar ASOs que vencem em até N dias")
    parser.add_argument("--headless", action="store_true", help="Executa navegador em modo headless")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    driver = build_driver(args.headless)
    try:
        driver.get(args.login_url)
        print("Faça login no eSocial no navegador aberto e pressione ENTER para continuar...", file=sys.stderr)
        input()

        if args.aso_url:
            driver.get(args.aso_url)

        WebDriverWait(driver, 30).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tr")) > 0)
        records = scrape_table_rows(driver)
        records = filter_due(records, args.due_days)

        out_json = Path(args.output_json).resolve()
        out_csv = Path(args.output_csv).resolve()
        write_json(records, out_json)
        write_csv(records, out_csv)

        print(f"{len(records)} registros exportados")
        print(f"JSON: {out_json}")
        print(f"CSV: {out_csv}")
        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
