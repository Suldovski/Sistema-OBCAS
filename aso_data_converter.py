#!/usr/bin/env python3
"""
Converte dados de ASO entre JSON/CSV e gera arquivo pronto para importação no Sistema-OBCAS.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


def norm_date(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def pick(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row and str(row[key]).strip():
            return str(row[key]).strip()
    return ""


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def convert(rows: list[dict]) -> list[dict]:
    output = []
    for row in rows:
        nome = pick(row, "nome", "NOME")
        re = pick(row, "re", "RE", "matricula", "MATRICULA", "matrícula", "MATRÍCULA")
        aso = norm_date(pick(row, "vencimento_aso", "vencimento aso", "VENCIMENTO ASO", "aso", "ASO"))
        if not nome:
            continue
        output.append(
            {
                "RE": re,
                "NOME": nome,
                "VENCIMENTO ASO": aso,
                "SITUACAO": pick(row, "status", "situacao", "SITUACAO"),
            }
        )
    return output


def save(rows: list[dict], output_path: Path) -> None:
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    fields = ["RE", "NOME", "VENCIMENTO ASO", "SITUACAO"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Converte dados de ASO para importação no Sistema-OBCAS")
    parser.add_argument("--input", required=True, help="Arquivo de entrada (.json ou .csv)")
    parser.add_argument("--output", required=True, help="Arquivo de saída (.json ou .csv)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    in_path = Path(args.input).resolve()
    out_path = Path(args.output).resolve()
    rows = load_rows(in_path)
    converted = convert(rows)
    save(converted, out_path)
    print(f"{len(converted)} registros convertidos em {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
