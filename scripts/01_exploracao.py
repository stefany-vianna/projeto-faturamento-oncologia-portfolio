import pandas as pd

arquivo = "data/raw/01_faturamento_sistema.xlsx"

df = pd.read_excel(arquivo)

print(df.head())

print("Quantidade de linhas e colunas:")
print(df.shape)

print("Colunas da base:")
print(df.columns)

print("Informações da base:")
df.info()

print("Valores nulos por coluna:")
print(df.isna().sum())

print("Quantidade de registros duplicados:")
print(df.duplicated().sum())

print("Registros duplicados:")
print(df[df.duplicated()])

duplicados = df[df.duplicated()]

print("Valor total dos registros duplicados:")
print(duplicados["VL_TOTAL_CONTA"].sum())

df_limpo = df.drop_duplicates().copy()

print("Quantidade de linhas após remover duplicados:")
print(df_limpo.shape)

print("Faturamento antes da limpeza:")
print(df["VL_TOTAL_CONTA"].sum())

print("Faturamento após a limpeza:")
print(round(df_limpo["VL_TOTAL_CONTA"].sum(), 2))

df_limpo["STATUS_ENVIO"] = df_limpo["DT_ENVIO_SISTEMA"].apply(
    lambda x: "Pendente de envio" if pd.isna(x) else "Enviado"
)

print("Status de envio:")
print(df_limpo["STATUS_ENVIO"].value_counts())

valor_pendente_envio = df_limpo.loc[
    df_limpo["STATUS_ENVIO"] == "Pendente de envio",
    "VL_TOTAL_CONTA"
].sum()

print("Valor pendente de envio:")
print(round(valor_pendente_envio, 2))

faturamento_total = df_limpo["VL_TOTAL_CONTA"].sum()

percentual_pendente = (
    valor_pendente_envio / faturamento_total
) * 100

print("Percentual do faturamento pendente de envio:")
print(round(percentual_pendente, 2), "%")

faturamento_convenio = (
    df_limpo.groupby("NM_CONVENIO")["VL_TOTAL_CONTA"]
    .sum()
    .sort_values(ascending=False)
)

print("Faturamento por convênio:")
print(faturamento_convenio)

participacao_convenio = (
    faturamento_convenio / faturamento_total
) * 100

print("Participação por convênio:")
print(participacao_convenio.round(2))

df_limpo["NM_CONVENIO_PADRAO"] = (
    df_limpo["NM_CONVENIO"]
    .str.strip()
    .str.upper()
)
print("Convênios após padronização:")
print(df_limpo["NM_CONVENIO_PADRAO"].unique())

faturamento_convenio = (
    df_limpo.groupby("NM_CONVENIO_PADRAO")["VL_TOTAL_CONTA"]
    .sum()
    .sort_values(ascending=False)
)

print("Faturamento por convênio após padronização:")
print(faturamento_convenio.round(2))
participacao_convenio = (
    faturamento_convenio / faturamento_total
) * 100

print("Participação por convênio após padronização:")
print(participacao_convenio.round(2))

top3_valor = faturamento_convenio.head(3).sum()

top3_percentual = (
    top3_valor / faturamento_total
) * 100

print("Faturamento dos 3 maiores convênios:")
print(round(top3_valor, 2))

print("Percentual dos 3 maiores convênios:")
print(round(top3_percentual, 2), "%")

#Como o faturamento evoluiu ao longo dos meses?#
#1 - criar uma coluna contendo apenas o mês da competência

df_limpo["MES_COMPETENCIA"] = (
    df_limpo["DT_COMPETENCIA"]
    .dt.to_period("M")
    .dt.to_timestamp()
)

#2- agrupamos por mês
faturamento_mensal = (
    df_limpo.groupby("MES_COMPETENCIA")["VL_TOTAL_CONTA"]
    .sum()
    .sort_index()
)

print("Faturamento mensal:")
print(faturamento_mensal.round(2))

#Quantidade de contas por mês
quantidade_mensal = (
    df_limpo.groupby("MES_COMPETENCIA")["ID_FATURAMENTO"]
    .count()
)

print("Quantidade de contas por mês:")
print(quantidade_mensal)

#Valor médio faturado por conta
ticket_medio_mensal = (
    faturamento_mensal / quantidade_mensal
)

print("Ticket médio mensal:")
print(ticket_medio_mensal.round(2))

#Variação mensal
variacao_mensal = faturamento_mensal.pct_change() * 100

print("Variação mensal do faturamento:")
print(variacao_mensal.round(2))

#Tabela de análise
resumo_mensal = pd.DataFrame({
    "FATURAMENTO": faturamento_mensal,
    "QUANTIDADE_CONTAS": quantidade_mensal,
    "TICKET_MEDIO": ticket_medio_mensal,
    "VARIACAO_PERCENTUAL": variacao_mensal
})

print("Resumo mensal:")
print(resumo_mensal.round(2))

#Em qual mês aconteceu o maior faturamento?
maior_faturamento = faturamento_mensal.max()
mes_maior_faturamento = faturamento_mensal.idxmax()

menor_faturamento = faturamento_mensal.min()
mes_menor_faturamento = faturamento_mensal.idxmin()

media_faturamento = faturamento_mensal.mean()

print("Maior faturamento mensal:")
print(mes_maior_faturamento)
print(round(maior_faturamento, 2))

print("Menor faturamento mensal:")
print(mes_menor_faturamento)
print(round(menor_faturamento, 2))

print("Média mensal de faturamento:")
print(round(media_faturamento, 2))

variacao_quantidade = quantidade_mensal.pct_change() * 100

variacao_ticket = ticket_medio_mensal.pct_change() * 100

resumo_mensal["VARIACAO_QUANTIDADE"] = variacao_quantidade
resumo_mensal["VARIACAO_TICKET"] = variacao_ticket
print("Análise das variações mensais:")
print(resumo_mensal.round(2))

print("Análise de agosto de 2026:")
print(resumo_mensal.loc["2026-08-01"])

#Faturamento por unidade e setor
faturamento_unidade = (
    df_limpo.groupby("UNIDADE")["VL_TOTAL_CONTA"]
    .sum()
    .sort_values(ascending=False)
)

print("Faturamento por unidade:")
print(faturamento_unidade.round(2))

participacao_unidade = (
    faturamento_unidade / faturamento_total
) * 100

print("Participação por unidade:")
print(participacao_unidade.round(2))

faturamento_setor = (
    df_limpo.groupby("SETOR")["VL_TOTAL_CONTA"]
    .sum()
    .sort_values(ascending=False)
)

print("Faturamento por setor:")
print(faturamento_setor.round(2))

participacao_setor = (
    faturamento_setor / faturamento_total
) * 100

print("Participação por setor:")
print(participacao_setor.round(2))