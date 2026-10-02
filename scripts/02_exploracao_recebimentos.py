import pandas as pd

arquivo = "data/raw/02_controle_recebimentos_manual.xlsx"

df_financeiro = pd.read_excel(
    arquivo,
    sheet_name="CONTROLE_MANUAL"
)

print("Primeiras linhas:")
print(df_financeiro.head())

print("Quantidade de linhas e colunas:")
print(df_financeiro.shape)

print("Colunas da base:")
print(df_financeiro.columns)

print("Informações da base:")
df_financeiro.info()

print("Valores nulos por coluna:")
print(df_financeiro.isna().sum())

print("Quantidade de registros duplicados:")
print(df_financeiro.duplicated().sum())

print("Exemplos da coluna DATA_GLOSA:")
print(
    df_financeiro.loc[
        df_financeiro["DATA_GLOSA"].notna(),
        "DATA_GLOSA"
    ].head(10)
)
print("Status existentes:")
print(df_financeiro["STATUS_MANUAL"].value_counts())

print("Quantidade com glosa inicial:")
print((df_financeiro["GLOSA_INICIAL"] > 0).sum())

print("Quantidade com glosa aceita/desconsiderada:")
print((df_financeiro["GLOSA_DESCONSIDERADA"] > 0).sum())

print("Quantidade com valor recursado:")
print((df_financeiro["VALOR_RECURSADO"] > 0).sum())

print("Quantidade com pagamento de recurso:")
print((df_financeiro["VALOR_PAGO_RECURSO"] > 0).sum())

df_financeiro_limpo = df_financeiro.copy()
df_financeiro_limpo["DATA_GLOSA"] = pd.to_datetime(
    df_financeiro_limpo["DATA_GLOSA"],
    unit="D",
    origin="1899-12-30",
    errors="coerce"
)
print("DATA_GLOSA após conversão:")
print(
    df_financeiro_limpo["DATA_GLOSA"]
    .dropna()
    .head(10)
)

print("Tipo da coluna DATA_GLOSA:")
print(df_financeiro_limpo["DATA_GLOSA"].dtype)

print("Quantidade de datas de glosa após conversão:")
print(df_financeiro_limpo["DATA_GLOSA"].notna().sum())

glosas = df_financeiro_limpo[
    df_financeiro_limpo["GLOSA_INICIAL"] > 0
].copy()

print("Primeiras guias com glosa:")
print(
    glosas[
        [
            "NR_GUIA",
            "GLOSA_INICIAL",
            "GLOSA_DESCONSIDERADA",
            "VALOR_RECURSADO",
            "VALOR_PAGO_RECURSO",
            "STATUS_MANUAL"
        ]
    ].head(10)
)
# Validar se a glosa inicial foi totalmente classificada
df_financeiro_limpo["DIFERENCA_GLOSA"] = (
    df_financeiro_limpo["GLOSA_INICIAL"]
    - df_financeiro_limpo["GLOSA_DESCONSIDERADA"]
    - df_financeiro_limpo["VALOR_RECURSADO"]
).round(2)

df_financeiro_limpo["REGRA_GLOSA_OK"] = (
    df_financeiro_limpo["DIFERENCA_GLOSA"].abs() <= 0.01
)

glosas = df_financeiro_limpo[
    df_financeiro_limpo["GLOSA_INICIAL"] > 0
].copy()

print("Validação da composição da glosa:")
print(glosas["REGRA_GLOSA_OK"].value_counts())

glosas_com_problema = glosas[
    glosas["REGRA_GLOSA_OK"] == False
]

print("Glosas com diferença:")
print(
    glosas_com_problema[
        [
            "NR_GUIA",
            "GLOSA_INICIAL",
            "GLOSA_DESCONSIDERADA",
            "VALOR_RECURSADO",
            "DIFERENCA_GLOSA"
        ]
    ]
)
df_financeiro_limpo["GLOSA_NAO_CLASSIFICADA"] = (
    df_financeiro_limpo["GLOSA_INICIAL"]
    - df_financeiro_limpo["GLOSA_DESCONSIDERADA"]
    - df_financeiro_limpo["VALOR_RECURSADO"]
).round(2)
print("Total de glosa inicial:")
print(round(df_financeiro_limpo["GLOSA_INICIAL"].sum(), 2))

print("Total de glosa aceita/desconsiderada:")
print(round(df_financeiro_limpo["GLOSA_DESCONSIDERADA"].sum(), 2))

print("Total recursado:")
print(round(df_financeiro_limpo["VALOR_RECURSADO"].sum(), 2))

print("Glosa NAO_CLASSIFICADA:")
print(round(df_financeiro_limpo["GLOSA_NAO_CLASSIFICADA"].sum(), 2))
print("Quantidade de glosas nao classificadas negativas:")
print(
    (
        df_financeiro_limpo["GLOSA_NAO_CLASSIFICADA"] < 0
    ).sum()
)
df_financeiro_limpo["STATUS_RECURSO"] = "SEM RECURSO"
df_financeiro_limpo.loc[
    df_financeiro_limpo["VALOR_RECURSADO"] > 0,
    "STATUS_RECURSO"
] = "PENDENTE"
df_financeiro_limpo.loc[
    df_financeiro_limpo["DATA_PAGAMENTO_RECURSO"].notna(),
    "STATUS_RECURSO"
] = "FINALIZADO"
print("Status dos recursos:")
print(df_financeiro_limpo["STATUS_RECURSO"].value_counts())

df_financeiro_limpo["RECURSO_PENDENTE"] = 0.0
df_financeiro_limpo.loc[
    df_financeiro_limpo["STATUS_RECURSO"] == "PENDENTE",
    "RECURSO_PENDENTE"
] = df_financeiro_limpo["VALOR_RECURSADO"]
print("Valor total de recursos pendentes:")
print(
    round(
        df_financeiro_limpo["RECURSO_PENDENTE"].sum(),
        2
    )
)
#Valor recursado - valor pago do recurso = glosa/perda do recurso
df_financeiro_limpo["PERDA_RECURSO"] = 0.0
df_financeiro_limpo.loc[
    df_financeiro_limpo["STATUS_RECURSO"] == "FINALIZADO",
    "PERDA_RECURSO"
] = (
    df_financeiro_limpo["VALOR_RECURSADO"]
    - df_financeiro_limpo["VALOR_PAGO_RECURSO"]
)
total_recursado = df_financeiro_limpo["VALOR_RECURSADO"].sum()

total_recuperado = df_financeiro_limpo["VALOR_PAGO_RECURSO"].sum()

total_perda_recurso = df_financeiro_limpo["PERDA_RECURSO"].sum()

print("Total recursado:")
print(round(total_recursado, 2))

print("Total recuperado em recursos:")
print(round(total_recuperado, 2))

print("Perda em recursos finalizados:")
print(round(total_perda_recurso, 2))

#valor recuperado/valor recursado já finalizado
taxa_recuperacao = (
    total_recuperado
    /
    df_financeiro_limpo.loc[
        df_financeiro_limpo["STATUS_RECURSO"] == "FINALIZADO",
        "VALOR_RECURSADO"
    ].sum()
) * 100

print("Taxa de recuperação dos recursos finalizados:")
print(round(taxa_recuperacao, 2), "%")

#Glosa aceita + Perda dos recursos finalizados = Perda definitiva conhecida #
total_glosa_aceita = (
    df_financeiro_limpo["GLOSA_DESCONSIDERADA"].sum()
)

perda_definitiva = (
    total_glosa_aceita
    + total_perda_recurso
)

print("Glosa aceita/desconsiderada:")
print(round(total_glosa_aceita, 2))

print("Perda definitiva conhecida:")
print(round(perda_definitiva, 2))

#Perda definitiva/glosa inicial * 100 = Percentual de perda definitiva conhecida até o momento#
percentual_perda_definitiva = (
    perda_definitiva
    / df_financeiro_limpo["GLOSA_INICIAL"].sum()
) * 100

print("Percentual de perda definitiva sobre a glosa inicial:")
print(round(percentual_perda_definitiva, 2), "%")

resumo_glosas = pd.DataFrame({
    "CATEGORIA": [
        "Perda definitiva",
        "Valor recuperado",
        "Recurso pendente",
        "Glosa não classificada"
    ],
    "VALOR": [
        perda_definitiva,
        total_recuperado,
        df_financeiro_limpo["RECURSO_PENDENTE"].sum(),
        df_financeiro_limpo["GLOSA_NAO_CLASSIFICADA"].sum()
    ]
})
total_glosa_inicial = df_financeiro_limpo["GLOSA_INICIAL"].sum()

resumo_glosas["PERCENTUAL"] = (
    resumo_glosas["VALOR"]
    / total_glosa_inicial
) * 100
print("Resumo das glosas:")
print(resumo_glosas.round(2))

print("Percentual total:")
print(round(resumo_glosas["PERCENTUAL"].sum(), 2), "%")