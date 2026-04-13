#!/usr/bin/env python3
"""
Extrator de vencimentos ASO via API eSocial com certificado digital.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from requests import Session
from requests_pkcs12 import Pkcs12Adapter


DEFAULT_DATE_KEYS = [
    "vencimento_aso",
    "vencimentoASO",
    "vencimentoAso",
    "data_vencimento_aso",
    "dataVencimentoAso",
    "data_vencimento",
    "dataVencimento",
    "vencimento",
]


@dataclass
class AsoRecord:
    cpf: str = ""
    nome: str = ""
    re: str = ""
    vencimento_aso: str = ""
    status: str = ""
    origem: str = "eSocial"


@dataclass
class Config:
    base_url: str
    auth_endpoint: str
    aso_endpoint: str
    cert_type: str
    pfx_path: str
    pfx_password: str
    cert_path: str
    key_path: str
    verify_ssl: bool
    headers: dict[str, str]
    auth_method: str
    aso_method: str
    auth_payload: dict[str, Any]
    aso_params: dict[str, Any]
    records_path: str
    date_key_candidates: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extrai vencimentos ASO do eSocial por certificado digital")
    parser.add_argument("--config", default="config.json", help="Arquivo JSON de configuração")
    parser.add_argument("--output-json", default="aso_esocial.json", help="Saída JSON")
    parser.add_argument("--output-csv", default="aso_esocial.csv", help="Saída CSV")
    parser.add_argument("--due-days", type=int, default=None, help="Filtra ASOs que vencem em até N dias")
    return parser.parse_args()


def load_config(path: Path) -> Config:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cert = payload.get("cert", {})
    endpoints = payload.get("endpoints", {})
    request_cfg = payload.get("request", {})
    mapping = payload.get("mapping", {})

    return Config(
        base_url=str(payload.get("base_url", "")).rstrip("/"),
        auth_endpoint=str(endpoints.get("auth", "")).strip(),
        aso_endpoint=str(endpoints.get("aso", "")).strip(),
        cert_type=str(cert.get("type", "pfx")).strip().lower(),
        pfx_path=str(cert.get("pfx_path", "")).strip(),
        pfx_password=str(cert.get("pfx_password", "")).strip(),
        cert_path=str(cert.get("cert_path", "")).strip(),
        key_path=str(cert.get("key_path", "")).strip(),
        verify_ssl=bool(request_cfg.get("verify_ssl", True)),
        headers={str(k): str(v) for k, v in dict(request_cfg.get("headers", {})).items()},
        auth_method=str(request_cfg.get("auth_method", "GET")).upper(),
        aso_method=str(request_cfg.get("aso_method", "GET")).upper(),
        auth_payload=dict(request_cfg.get("auth_payload", {})),
        aso_params=dict(request_cfg.get("aso_params", {})),
        records_path=str(mapping.get("records_path", "")).strip(),
        date_key_candidates=[str(x) for x in mapping.get("date_keys", DEFAULT_DATE_KEYS)],
    )


def build_url(base_url: str, endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"{base_url}/{endpoint.lstrip('/')}"


def get_by_path(payload: Any, path: str) -> Any:
    current = payload
    for part in [p for p in path.split(".") if p]:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            if idx >= len(current):
                return None
            current = current[idx]
        else:
            return None
    return current


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            result.update(flatten_dict(value, full_key))
        else:
            result[full_key.lower()] = "" if value is None else str(value).strip()
            result[str(key).lower()] = "" if value is None else str(value).strip()
    return result


def parse_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    try:
        normalized = text.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


def normalize_date(value: str) -> str:
    dt = parse_date(value)
    return dt.isoformat() if dt else ""


def find_records(payload: Any, date_keys: list[str]) -> list[dict[str, Any]]:
    keys = {k.lower() for k in date_keys}
    found: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            lowered = {str(k).lower() for k in node.keys()}
            if lowered.intersection(keys):
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def extract_records(payload: Any, cfg: Config) -> list[AsoRecord]:
    if cfg.records_path:
        raw_records = get_by_path(payload, cfg.records_path)
        if not isinstance(raw_records, list):
            raw_records = []
    else:
        raw_records = find_records(payload, cfg.date_key_candidates)

    records: list[AsoRecord] = []
    date_keys = [k.lower() for k in cfg.date_key_candidates]

    for item in raw_records:
        if not isinstance(item, dict):
            continue
        flat = flatten_dict(item)
        venc = ""
        for key in date_keys:
            venc = flat.get(key, "")
            if venc:
                break
        normalized_venc = normalize_date(venc)
        if not normalized_venc:
            continue

        records.append(
            AsoRecord(
                cpf=flat.get("cpf", flat.get("trabalhador.cpf", "")),
                nome=flat.get("nome", flat.get("trabalhador.nome", "")),
                re=flat.get("re", flat.get("matricula", flat.get("trabalhador.matricula", ""))),
                vencimento_aso=normalized_venc,
                status=flat.get("status", flat.get("situacao", "")),
            )
        )

    return records


def filter_due(records: list[AsoRecord], due_days: int | None) -> list[AsoRecord]:
    if due_days is None:
        return records
    limit = date.today() + timedelta(days=due_days)
    return [r for r in records if parse_date(r.vencimento_aso) and parse_date(r.vencimento_aso) <= limit]


def write_json(records: list[AsoRecord], path: Path) -> None:
    path.write_text(json.dumps([asdict(row) for row in records], ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(records: list[AsoRecord], path: Path) -> None:
    fields = ["cpf", "nome", "re", "vencimento_aso", "status", "origem"]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow(asdict(row))


def build_session(cfg: Config) -> Session:
    session = requests.Session()
    session.headers.update(cfg.headers)

    if cfg.cert_type == "pfx":
        if not cfg.pfx_path or not cfg.pfx_password:
            raise ValueError("Para certificado PFX, configure cert.pfx_path e cert.pfx_password")
        if not Path(cfg.pfx_path).exists():
            raise FileNotFoundError(f"Certificado não encontrado: {cfg.pfx_path}")
        session.mount(
            "https://",
            Pkcs12Adapter(pkcs12_filename=cfg.pfx_path, pkcs12_password=cfg.pfx_password),
        )
    elif cfg.cert_type == "pem":
        if not cfg.cert_path:
            raise ValueError("Para certificado PEM, configure cert.cert_path")
        if cfg.key_path:
            session.cert = (cfg.cert_path, cfg.key_path)
        else:
            session.cert = cfg.cert_path
    else:
        raise ValueError("cert.type deve ser 'pfx' ou 'pem'")

    session.verify = cfg.verify_ssl
    return session


def authenticate(session: Session, cfg: Config) -> None:
    if not cfg.auth_endpoint:
        return
    url = build_url(cfg.base_url, cfg.auth_endpoint)
    kwargs: dict[str, Any] = {"timeout": 60}
    if cfg.auth_payload:
        kwargs["json"] = cfg.auth_payload
    response = session.request(cfg.auth_method, url, **kwargs)
    response.raise_for_status()


def fetch_aso_data(session: Session, cfg: Config) -> Any:
    if not cfg.aso_endpoint:
        raise ValueError("Configure endpoints.aso no arquivo de configuração")

    url = build_url(cfg.base_url, cfg.aso_endpoint)
    response = session.request(cfg.aso_method, url, params=cfg.aso_params, timeout=60)
    response.raise_for_status()

    try:
        return response.json()
    except ValueError as exc:
        raise ValueError("A API retornou conteúdo não JSON") from exc


def main() -> int:
    args = parse_args()
    cfg_path = Path(args.config).resolve()
    cfg = load_config(cfg_path)

    session = build_session(cfg)
    authenticate(session, cfg)
    payload = fetch_aso_data(session, cfg)

    records = extract_records(payload, cfg)
    records = filter_due(records, args.due_days)

    out_json = Path(args.output_json).resolve()
    out_csv = Path(args.output_csv).resolve()
    write_json(records, out_json)
    write_csv(records, out_csv)

    print(f"{len(records)} ASOs exportados")
    print(f"JSON: {out_json}")
    print(f"CSV: {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
