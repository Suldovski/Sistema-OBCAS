# Integração ASO eSocial (Sistema-OBCAS)

Este repositório agora inclui uma automação simples para coletar vencimentos de ASO no eSocial e importar no `index.html`.

## Arquivos adicionados

- `esocial_aso_scraper.py`  
  Abre o eSocial com Selenium, aguarda login manual, lê tabela de ASO e exporta:
  - `aso_esocial.json`
  - `aso_esocial.csv`

- `aso_data_converter.py`  
  Converte JSON/CSV do scraper para um formato pronto para importação no OBCAS:
  - colunas: `RE`, `NOME`, `VENCIMENTO ASO`, `SITUACAO`

- `requirements.txt`  
  Dependências Python.

## Pré-requisitos

1. Python 3.10+
2. Google Chrome instalado
3. Driver do Chrome compatível (ChromeDriver)

Instalação:

```bash
pip install -r requirements.txt
```

## 1) Extrair dados no eSocial

```bash
python esocial_aso_scraper.py \
  --login-url "https://www.esocial.gov.br/" \
  --aso-url "URL_DA_TELA_DE_ASO" \
  --due-days 60 \
  --output-json aso_esocial.json \
  --output-csv aso_esocial.csv
```

Fluxo:
1. O navegador abre.
2. Faça login no eSocial manualmente.
3. Volte ao terminal e pressione `ENTER`.
4. O script extrai a tabela e gera CSV/JSON.

## 2) Converter para importação no Sistema-OBCAS

Exemplo com JSON:

```bash
python aso_data_converter.py --input aso_esocial.json --output aso_import_obcas.csv
```

Exemplo com CSV:

```bash
python aso_data_converter.py --input aso_esocial.csv --output aso_import_obcas.csv
```

## 3) Importar no HTML atual

No `index.html`, use o botão de importação de planilha e selecione o arquivo convertido.

O sistema já reconhece a coluna `VENCIMENTO ASO` e preenche automaticamente o campo **Venc. ASO** dos colaboradores importados.
