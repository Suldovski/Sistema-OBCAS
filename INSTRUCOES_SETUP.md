# Instruções de Setup Seguro (eSocial ASO)

## 1) Instalar dependências

```bash
pip install -r requirements.txt
```

## 2) Preparar configuração local

```bash
cp config_example.json config.json
```

> `config.json` é local e não deve ser versionado.

## 3) Definir variáveis de ambiente sensíveis

Exemplo Linux/macOS:

```bash
export ESOCIAL_PFX_PATH="/caminho/seguro/certificado.pfx"
export ESOCIAL_PFX_PASSWORD="SENHA_DO_CERTIFICADO"
export ESOCIAL_CNPJ="00.000.000/0000-00"
```

Exemplo PowerShell:

```powershell
$env:ESOCIAL_PFX_PATH="C:\certificados\certificado.pfx"
$env:ESOCIAL_PFX_PASSWORD="SENHA_DO_CERTIFICADO"
$env:ESOCIAL_CNPJ="00.000.000/0000-00"
```

## 4) Executar extração

```bash
python esocial_scraper.py --config config.json --output-json aso_esocial.json --output-csv aso_esocial.csv
```

Filtrar vencimentos nos próximos 60 dias:

```bash
python esocial_scraper.py --config config.json --due-days 60
```

## 5) Validar saída e proteção de dados

- Resultado esperado: exportação em CSV/JSON de até 226 funcionários (conforme parâmetros da API).
- Confirme que arquivos sensíveis não aparecem no `git status`.
- Nunca compartilhe certificado, senha ou credenciais fora do ambiente autorizado.
