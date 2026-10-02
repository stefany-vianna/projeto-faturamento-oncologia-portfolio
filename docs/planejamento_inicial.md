# Analise Financeira do Faturamento de uma Clinica Oncologica

Projeto de portfolio com dados **100% ficticios**, inspirado em um processo real de acompanhamento de faturamento, recebimentos e glosas.

## Cenario
A area de faturamento fornece uma exportacao do sistema e mantem uma segunda planilha manual para acompanhar recebimentos, glosas, recursos, impostos e notas fiscais. O objetivo do projeto e tratar e integrar essas fontes com Python e criar uma base analitica para um dashboard financeiro.

## Fontes
- `data/raw/01_faturamento_sistema.xlsx`: exportacao simulada do sistema.
- `data/raw/02_controle_recebimentos_manual.xlsx`: controle manual simulado.

## Principais analises planejadas
- Faturamento bruto e liquido
- Valor recebido e valor em aberto
- Glosa inicial, glosa liquida e recuperacao de glosas
- Prazo medio de envio
- Prazo medio de recebimento / aging
- Receita por competencia, operadora, unidade e tipo de faturamento
- Faixas de atraso (0-30, 31-60, 61-90 e 90+ dias)
- Indicadores de qualidade do processo: contas sem envio, sem controle manual e duplicidades

> Nenhum dado real de paciente, clinica ou operadora foi utilizado nestes arquivos.
