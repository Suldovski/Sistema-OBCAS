# Extração de Vencimento ASO (eSocial com certificado digital)

Este guia mostra como usar o `esocial_scraper.py` para autenticar com certificado digital (.pfx ou .pem), consultar dados do eSocial e exportar vencimentos de ASO em CSV/JSON.

## Arquivos

- `esocial_scraper.py` — script principal de extração
- `config_example.json` — modelo de configuração
- `requirements.txt` — dependências Python

## Pré-requisitos

- Python 3.10+
- Certificado digital válido (A1) em `.pfx` ou `.pem`
- Endpoint de API do eSocial habilitado para sua empresa

## Instalação

```bash
pip install -r requirements.txt
```

## Preparar o certificado

### Opção 1: usar `.pfx` (recomendado)
No `config.json`:

```json
"cert": {
  "type": "pfx",
  "pfx_path": "/caminho/certificado.pfx",
  "pfx_password": "SENHA"
}
```

### Opção 2: usar `.pem`
No `config.json`:

```json
"cert": {
  "type": "pem",
  "cert_path": "/caminho/certificado.pem",
  "key_path": "/caminho/chave.key"
}
```

## Configuração

1. Copie o modelo:

```bash
cp config_example.json config.json
```

2. Ajuste:
- `base_url`
- `endpoints.auth` e `endpoints.aso`
- `request.aso_params`
- `mapping.records_path` e `mapping.date_keys` conforme retorno real da sua API
- mantenha segredos (senha, caminho do certificado, CNPJ) em variáveis de ambiente e use referências `${NOME_DA_VARIAVEL}` no `config.json`

## Executar

```bash
python esocial_scraper.py --config config.json --output-json aso_esocial.json --output-csv aso_esocial.csv
```

Filtrar apenas ASOs vencendo nos próximos 60 dias:

```bash
python esocial_scraper.py --config config.json --due-days 60
```

## Saída

- JSON com campos: `cpf`, `nome`, `re`, `vencimento_aso`, `status`, `origem`
- CSV com os mesmos campos

Esses dados podem ser convertidos para o layout do Sistema-OBCAS com o script já existente (`aso_data_converter.py`).

## Troubleshooting (certificado)

- **`Certificado não encontrado`**: confira caminho absoluto do arquivo.
- **`cert.type deve ser 'pfx' ou 'pem'`**: ajuste o tipo no config.
- **`SSL: CERTIFICATE_VERIFY_FAILED`**:
  - confirme cadeia do certificado;
  - mantenha `verify_ssl: true` em produção;
  - valide relógio/data do sistema.
- **`401/403` na autenticação**:
  - verifique permissão do certificado no ambiente eSocial;
  - revise `endpoints.auth` e cabeçalhos.
- **`A API retornou conteúdo não JSON`**:
  - confirme endpoint e método HTTP;
  - valide se o endpoint exige parâmetros adicionais.

## Segurança

- Nunca commite `config.json`, certificados ou arquivos de credenciais.
- O projeto já inclui regras no `.gitignore` para bloquear esses arquivos.
- Consulte `README_SEGURANÇA.md` e `INSTRUCOES_SETUP.md` antes do primeiro uso.
