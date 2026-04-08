# Sistema de Apuramento de Votos de Restaurantes

Projeto em Python para tratar submissões CSV de votação de pratos por restaurante, remover votos duplicados e gerar rankings finais em CSV e PDF.

## Visão Geral

Este projeto tem dois scripts principais:

1. `remover_duplicadas.py`
Processa ficheiros CSV, remove duplicados por email e guarda os ficheiros limpos em `output_limpos/`.

2. `processar_votos.py`
Lê os CSV (originais ou limpos), identifica a coluna de prato, calcula o ranking por restaurante e exporta:
- ranking em CSV
- relatório em PDF

## Funcionalidades

- Normalização flexível de nomes de colunas
- Remoção de votos duplicados por `Email Address` (mantém o registo mais antigo por `Timestamp`)
- Ranking por prato para cada restaurante
- Exportação de relatório PDF com resumo geral e detalhe por restaurante

## Requisitos

- Python 3.9+
- Pacotes:
  - `pandas`
  - `chardet`
  - `reportlab`

## Instalação

Na pasta do projeto, instala as dependências:

```bash
pip install pandas chardet reportlab
```

Se estiveres no Windows e o `pip` não estiver no PATH:

```powershell
py -m pip install pandas chardet reportlab
```

## Como Usar

### Passo 1 (Opcional): Limpar duplicados

Executa:

```bash
python remover_duplicadas.py
```

O script:
- percorre recursivamente os CSV na pasta atual
- ignora a pasta `output_limpos`
- converte `Timestamp` para data/hora
- ordena do mais antigo para o mais recente
- remove duplicados por `Email Address`, mantendo o primeiro

Saida: ficheiros limpos em `output_limpos/`.

### Passo 2: Gerar ranking e relatorio

#### Opção A: processar CSV da pasta atual

```bash
python processar_votos.py
```

#### Opção B: processar uma pasta especifica

```bash
python processar_votos.py output_limpos
```

#### Opção C: processar ficheiros especificos

```bash
python processar_votos.py "Submissoes Feitas - Restaurante Céu.csv" "Submissoes Feitas - Restaurante Tasca Rasca.csv"
```

## Formato Esperado dos CSV

O script tenta encontrar automaticamente colunas equivalentes a:

- `timestamp`: `timestamp`, `data`, `date`
- `email`: `email address`, `email`, `e-mail`
- `prato`: `escolha o seu prato favorito:`, `prato`, `dish`, `escolha`
- `consent` (opcional): `consentimento`, `consent`

Notas:
- A coluna de prato é obrigatória para gerar ranking.
- A coluna de email é usada para contagem de emails únicos.

## Ficheiros Gerados

Ao correr `processar_votos.py`, são gerados:

- `ranking_restaurantes_YYYYMMDD_HHMMSS.csv`
- `ranking_restaurantes_YYYYMMDD_HHMMSS.pdf`

Os nomes incluem timestamp para não sobrescrever resultados anteriores.

## Problemas Comuns

### "Nenhum ficheiro CSV encontrado"

- Confirma se existem `.csv` na pasta onde executaste o comando.
- Ou passa explicitamente uma pasta/ficheiros no comando.

### "Coluna de prato não encontrada"

- Verifica o cabeçalho do CSV.
- Ajusta os nomes possíveis em `COLUNAS["prato"]` no script `processar_votos.py`.

### Erros de leitura de ficheiro

- Verifica se o CSV não está corrompido.
- Confirma separadores e cabeçalhos.

## Fluxo Recomendado

1. Colocar todos os CSV brutos na pasta do projeto.
2. Executar `remover_duplicadas.py`.
3. Executar `processar_votos.py output_limpos`.



