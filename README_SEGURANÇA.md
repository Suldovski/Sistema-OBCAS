# README de Segurança - Extração ASO eSocial

Este projeto foi estruturado para impedir exposição de dados sensíveis durante a extração de vencimentos de ASO.

## Princípios adotados

1. Certificado digital e credenciais **ficam somente em ambiente local**.
2. Dados sensíveis **não são versionados** no GitHub.
3. Configuração de exemplo usa apenas placeholders, sem valores reais.
4. Segredos são carregados por variáveis de ambiente no runtime.

## O que nunca deve ser commitado

- Arquivos de certificado: `.pfx`, `.p12`, `.pem`, `.key`, `.crt`, `.cer`
- Arquivo `config.json` local
- Credenciais de Firebase/Service Account
- Arquivos `.env` reais

## Controles implementados no repositório

- `.gitignore` bloqueando arquivos sensíveis e saídas locais.
- `config_example.json` como template seguro.
- `esocial_scraper.py` com suporte a `${VARIAVEL}` para injeção segura de segredos por ambiente.

## Boas práticas operacionais

- Use usuário/sessão dedicada para execução automatizada.
- Restrinja permissões do certificado (menor privilégio).
- Ative rotação periódica de certificados e credenciais.
- Revise `git status` antes de cada commit para evitar vazamentos.

## Resposta a incidente

Se qualquer segredo for exposto:

1. Revogue imediatamente certificado/credencial afetada.
2. Gere novo segredo e atualize variáveis locais.
3. Remova histórico exposto do repositório, quando aplicável.
4. Registre o incidente para auditoria.
