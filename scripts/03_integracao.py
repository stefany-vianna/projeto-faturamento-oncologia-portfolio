import pandas as pd

import os

arquivo_faturamento = "data/raw/01_faturamento_sistema.xlsx"
arquivo_financeiro = "data/raw/02_controle_recebimentos_manual.xlsx"

df_faturamento = pd.read_excel(arquivo_faturamento)

df_financeiro = pd.read_excel(
    arquivo_financeiro,
    sheet_name="CONTROLE_MANUAL"
)
#Remove as duplicadas
df_faturamento = df_faturamento.drop_duplicates().copy()

#Existe alguma guia repetida dentro de cada base?
print("Guias duplicadas na base de faturamento:")
print(
    df_faturamento.duplicated(
        subset=["NR_GUIA"]
    ).sum()
)
#contas guias únicas em cada base
print("Guias duplicadas na base financeira:")
print(
    df_financeiro.duplicated(
        subset=["NR_GUIA"]
    ).sum()
)
print("Guias únicas no faturamento:")
print(df_faturamento["NR_GUIA"].nunique())

print("Guias únicas no financeiro:")
print(df_financeiro["NR_GUIA"].nunique())

#Padronizar a chave
df_faturamento["NR_GUIA"] = (
    df_faturamento["NR_GUIA"]
    .str.strip()
    .str.upper()
)

df_financeiro["NR_GUIA"] = (
    df_financeiro["NR_GUIA"]
    .str.strip()
    .str.upper()
)

#Primeira integração

df_integrado = pd.merge(
    df_faturamento,
    df_financeiro,
    on="NR_GUIA",
    how="left",
    validate="one_to_one",
    indicator=True
)
print("Quantidade de linhas após o merge:")
print(df_integrado.shape)

print("Resultado do cruzamento:")
print(df_integrado["_merge"].value_counts())

#Quais guias não foram encontradas na base financeira? (left_only)
guias_sem_financeiro = df_integrado[
    df_integrado["_merge"] == "left_only"
]

print("Quantidade de guias sem registro financeiro:")
print(guias_sem_financeiro.shape[0])

print("Exemplos de guias sem registro financeiro:")
print(
    guias_sem_financeiro[
        [
            "NR_GUIA",
            "NM_CONVENIO",
            "VL_TOTAL_CONTA",
            "DT_COMPETENCIA"
        ]
    ].head(10)
)
#Usado left pois não queremos perder nenhuma guia do faturamento, mesmo que não tenha registro financeiro.

valor_sem_financeiro = df_integrado.loc[
    df_integrado["_merge"] == "left_only",
    "VL_TOTAL_CONTA"
].sum()

print("Valor faturado sem acompanhamento financeiro:")
print(round(valor_sem_financeiro, 2))

faturamento_total_integrado = df_integrado["VL_TOTAL_CONTA"].sum()

percentual_sem_financeiro = (
    valor_sem_financeiro
    / faturamento_total_integrado
) * 100

print("Percentual do faturamento sem acompanhamento financeiro:")
print(round(percentual_sem_financeiro, 2), "%")

df_integrado["STATUS_ACOMPANHAMENTO_FINANCEIRO"] = (
    df_integrado["_merge"].apply(
        lambda x:
        "COM ACOMPANHAMENTO"
        if x == "both"
        else "SEM ACOMPANHAMENTO"
    )
)

print("Status de acompanhamento financeiro:")
print(
    df_integrado["STATUS_ACOMPANHAMENTO_FINANCEIRO"]
    .value_counts()
)

#INTEGRAR TERCEIRA BASE , PRAZOS.

arquivo_prazos = "data/raw/03_prazos_convenios.xlsx"

df_prazos = pd.read_excel(arquivo_prazos)
df_integrado["NM_CONVENIO_PADRAO"] = (
    df_integrado["NM_CONVENIO"]
    .str.strip()
    .str.upper()
)
print("Tabela de prazos:")
print(df_prazos)

print("Convênios duplicados na tabela de prazos:")
print(
    df_prazos.duplicated(
        subset=["NM_CONVENIO_PADRAO"]
    ).sum()
)

print("Quantidade de convênios na tabela de prazos:")
print(df_prazos["NM_CONVENIO_PADRAO"].nunique())

df_final = pd.merge(
    df_integrado,
    df_prazos,
    on="NM_CONVENIO_PADRAO",
    how="left",
    validate="many_to_one",
    indicator="merge_prazos"
)
print("Quantidade de linhas após incluir os prazos:")
print(df_final.shape)

print("Resultado do cruzamento com os prazos:")
print(df_final["merge_prazos"].value_counts())

#Algum convênio ficou sem prazo? zero=nenhum.
convenios_sem_prazo = df_final[
    df_final["merge_prazos"] == "left_only"
]

print("Quantidade de registros sem prazo contratual:")
print(convenios_sem_prazo.shape[0])

#Prazo começa em Lote enviado - a partir da data em que a cobrança foi enviada à operadora.

df_final["DATA_LIMITE_PAGAMENTO"] = (
    df_final["LOTE_ENVIADO_EM"]
    + pd.to_timedelta(
        df_final["PRAZO_PAGAMENTO_COMPETENCIA_DIAS"],
        unit="D"
    )
)
print("Exemplos de prazos de pagamento:")

print(
    df_final[
        [
            "NR_GUIA",
            "NM_CONVENIO_PADRAO",
            "LOTE_ENVIADO_EM",
            "PRAZO_PAGAMENTO_COMPETENCIA_DIAS",
            "DATA_LIMITE_PAGAMENTO",
            "PAGO_EM"
        ]
    ].head(10)
)

df_final["STATUS_PRAZO_PAGAMENTO"] = "NAO AVALIADO"
df_final.loc[
    (df_final["PAGO_EM"].notna())
    &
    (
        df_final["PAGO_EM"]
        <= df_final["DATA_LIMITE_PAGAMENTO"]
    ),
    "STATUS_PRAZO_PAGAMENTO"
] = "PAGO NO PRAZO"
df_final.loc[
    (df_final["PAGO_EM"].notna())
    &
    (
        df_final["PAGO_EM"]
        > df_final["DATA_LIMITE_PAGAMENTO"]
    ),
    "STATUS_PRAZO_PAGAMENTO"
] = "PAGO EM ATRASO"
print("Status do prazo de pagamento:")

print(
    df_final["STATUS_PRAZO_PAGAMENTO"]
    .value_counts()
)
#Quantos dias atrasou?

df_final["DIAS_ATRASO_PAGAMENTO"] = (
    df_final["PAGO_EM"]
    - df_final["DATA_LIMITE_PAGAMENTO"]
).dt.days
df_final.loc[
    df_final["DIAS_ATRASO_PAGAMENTO"] < 0,
    "DIAS_ATRASO_PAGAMENTO"
] = 0

total_pagamentos_com_prazo_avaliado = (
    df_final["STATUS_PRAZO_PAGAMENTO"]
    != "NAO AVALIADO"
).sum()

pagamentos_no_prazo = (
    df_final["STATUS_PRAZO_PAGAMENTO"]
    == "PAGO NO PRAZO"
).sum()

percentual_no_prazo = (
    pagamentos_no_prazo
    / total_pagamentos_com_prazo_avaliado
) * 100

print("Pagamentos avaliados:")
print(total_pagamentos_com_prazo_avaliado)

print("Pagamentos no prazo:")
print(pagamentos_no_prazo)

print("Percentual de pagamentos dentro do SLA:")
print(round(percentual_no_prazo, 2), "%")

atraso_medio = df_final.loc[
    df_final["STATUS_PRAZO_PAGAMENTO"] == "PAGO EM ATRASO",
    "DIAS_ATRASO_PAGAMENTO"
].mean()

print("Atraso médio dos pagamentos atrasados:")
print(round(atraso_medio, 2), "dias")


sla_convenio = (
    df_final[
        df_final["STATUS_PRAZO_PAGAMENTO"] != "NAO AVALIADO"
    ]
    .groupby("NM_CONVENIO_PADRAO")
    .agg(
        PAGAMENTOS_AVALIADOS=("NR_GUIA", "count"),
        PAGAMENTOS_NO_PRAZO=(
            "STATUS_PRAZO_PAGAMENTO",
            lambda x: (x == "PAGO NO PRAZO").sum()
        ),
        PAGAMENTOS_ATRASADOS=(
            "STATUS_PRAZO_PAGAMENTO",
            lambda x: (x == "PAGO EM ATRASO").sum()
        ),
        ATRASO_MEDIO_DIAS=(
            "DIAS_ATRASO_PAGAMENTO",
            lambda x: x[x > 0].mean()
        )
    )
)

sla_convenio["PERCENTUAL_NO_PRAZO"] = (
    sla_convenio["PAGAMENTOS_NO_PRAZO"]
    / sla_convenio["PAGAMENTOS_AVALIADOS"]
) * 100

print("SLA por convênio:")
print(
    sla_convenio
    .round(2)
    .sort_values(
        by="PERCENTUAL_NO_PRAZO",
        ascending=False
    )
)

#Quantos dias decorreram entre o recebimento da glosa e o envio do recurso?

df_final["DATA_GLOSA"] = pd.to_datetime(
    df_final["DATA_GLOSA"],
    unit="D",
    origin="1899-12-30",
    errors="coerce"
)
df_final["DATA_LIMITE_RECURSO_CLINICA"] = (
    df_final["DATA_GLOSA"]
    + pd.to_timedelta(
        df_final["PRAZO_CLINICA_RECURSAR_DIAS"],
        unit="D"
    )
)
df_final["STATUS_PRAZO_RECURSO_CLINICA"] = "NAO AVALIADO"
df_final.loc[
    (df_final["DATA_RECURSO"].notna())
    &
    (
        df_final["DATA_RECURSO"]
        <= df_final["DATA_LIMITE_RECURSO_CLINICA"]
    ),
    "STATUS_PRAZO_RECURSO_CLINICA"
] = "RECURSO NO PRAZO"
df_final.loc[
    (df_final["DATA_RECURSO"].notna())
    &
    (
        df_final["DATA_RECURSO"]
        > df_final["DATA_LIMITE_RECURSO_CLINICA"]
    ),
    "STATUS_PRAZO_RECURSO_CLINICA"
] = "RECURSO EM ATRASO"
print("Prazo da clínica para recorrer:")

print(
    df_final["STATUS_PRAZO_RECURSO_CLINICA"]
    .value_counts()
)
df_final["DIAS_PARA_RECURSAR"] = (
    df_final["DATA_RECURSO"]
    - df_final["DATA_GLOSA"]
).dt.days

recursos_avaliados = (
    df_final["STATUS_PRAZO_RECURSO_CLINICA"]
    != "NAO AVALIADO"
).sum()

recursos_no_prazo = (
    df_final["STATUS_PRAZO_RECURSO_CLINICA"]
    == "RECURSO NO PRAZO"
).sum()

percentual_recursos_no_prazo = (
    recursos_no_prazo
    / recursos_avaliados
) * 100

print("Recursos avaliados:")
print(recursos_avaliados)

print("Recursos enviados no prazo:")
print(recursos_no_prazo)

print("Percentual de recursos dentro do SLA:")
print(round(percentual_recursos_no_prazo, 2), "%")

#Quantos dias a clínica leva, em média, para recorrer?
#Quantos dias de atraso ocorreram quando a clínica perdeu o prazo?

tempo_medio_recurso = df_final.loc[
    df_final["DATA_RECURSO"].notna(),
    "DIAS_PARA_RECURSAR"
].mean()

print("Tempo médio para recorrer:")
print(round(tempo_medio_recurso, 2), "dias")

df_final["DIAS_ATRASO_RECURSO_CLINICA"] = (
    df_final["DATA_RECURSO"]
    - df_final["DATA_LIMITE_RECURSO_CLINICA"]
).dt.days
atraso_medio_recurso = df_final.loc[
    df_final["STATUS_PRAZO_RECURSO_CLINICA"]
    == "RECURSO EM ATRASO",
    "DIAS_ATRASO_RECURSO_CLINICA"
].mean()

print("Atraso médio dos recursos enviados fora do prazo:")
print(round(atraso_medio_recurso, 2), "dias")

#DIAS_PARA_RECURSAR > tempo total entre a glosa e o recurso
#DIAS_ATRASO_RECURSO_CLINICA > somente quanto ultrapassou o prazo contratual

df_final["DATA_LIMITE_PAGAMENTO_RECURSO"] = (
    df_final["DATA_RECURSO"]
    + pd.to_timedelta(
        df_final["PRAZO_PAGAMENTO_RECURSO_DIAS"],
        unit="D"
    )
)
df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"] = "SEM RECURSO"

#recursos existentes mas ainda não pagos
df_final.loc[
    (df_final["DATA_RECURSO"].notna())
    &
    (df_final["DATA_PAGAMENTO_RECURSO"].isna()),
    "STATUS_PRAZO_PAGAMENTO_RECURSO"
] = "RECURSO PENDENTE"

#Pagos dentro do prazo:
df_final.loc[
    (df_final["DATA_PAGAMENTO_RECURSO"].notna())
    &
    (
        df_final["DATA_PAGAMENTO_RECURSO"]
        <= df_final["DATA_LIMITE_PAGAMENTO_RECURSO"]
    ),
    "STATUS_PRAZO_PAGAMENTO_RECURSO"
] = "PAGO NO PRAZO"

#Pagos depois do prazo:
df_final.loc[
    (df_final["DATA_PAGAMENTO_RECURSO"].notna())
    &
    (
        df_final["DATA_PAGAMENTO_RECURSO"]
        > df_final["DATA_LIMITE_PAGAMENTO_RECURSO"]
    ),
    "STATUS_PRAZO_PAGAMENTO_RECURSO"
] = "PAGO EM ATRASO"

print("Prazo de pagamento dos recursos:")

print(
    df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"]
    .value_counts()
)

#Depois do recurso, quantos dias a operadora levou para pagar?
df_final["DIAS_PAGAMENTO_RECURSO"] = (
    df_final["DATA_PAGAMENTO_RECURSO"]
    - df_final["DATA_RECURSO"]
).dt.days

df_final["DIAS_ATRASO_PAGAMENTO_RECURSO"] = (
    df_final["DATA_PAGAMENTO_RECURSO"]
    - df_final["DATA_LIMITE_PAGAMENTO_RECURSO"]
).dt.days

df_final.loc[
    df_final["DIAS_ATRASO_PAGAMENTO_RECURSO"] < 0,
    "DIAS_ATRASO_PAGAMENTO_RECURSO"
] = 0

#Pendentes não entram nesse indicador
recursos_pagamento_avaliado = df_final[
    df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"].isin(
        ["PAGO NO PRAZO", "PAGO EM ATRASO"]
    )
].shape[0]

recursos_pagos_no_prazo = (
    df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"]
    == "PAGO NO PRAZO"
).sum()

percentual_pagamento_recurso_no_prazo = (
    recursos_pagos_no_prazo
    / recursos_pagamento_avaliado
) * 100

print("Recursos com pagamento avaliado:")
print(recursos_pagamento_avaliado)

print("Recursos pagos no prazo:")
print(recursos_pagos_no_prazo)

print("Percentual de recursos pagos dentro do SLA:")
print(round(percentual_pagamento_recurso_no_prazo, 2), "%")

tempo_medio_pagamento_recurso = df_final.loc[
    df_final["DATA_PAGAMENTO_RECURSO"].notna(),
    "DIAS_PAGAMENTO_RECURSO"
].mean()

print("Tempo médio para pagamento do recurso:")
print(round(tempo_medio_pagamento_recurso, 2), "dias")

atraso_medio_pagamento_recurso = df_final.loc[
    df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"]
    == "PAGO EM ATRASO",
    "DIAS_ATRASO_PAGAMENTO_RECURSO"
].mean()

print("Atraso médio dos pagamentos de recurso:")
print(round(atraso_medio_pagamento_recurso, 2), "dias")

#Usar a data mais recente existente na própria base como referência. Até qual data esta base possui informações?#

data_corte_analise = df_final[
    [
        "PAGO_EM",
        "DATA_GLOSA",
        "DATA_RECURSO",
        "DATA_PAGAMENTO_RECURSO"
    ]
].max().max()

print("Data de corte da análise:")
print(data_corte_analise)

df_final["STATUS_RECURSO_PENDENTE"] = "NAO SE APLICA"
df_final.loc[
    (
        df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"]
        == "RECURSO PENDENTE"
    )
    &
    (
        data_corte_analise
        <= df_final["DATA_LIMITE_PAGAMENTO_RECURSO"]
    ),
    "STATUS_RECURSO_PENDENTE"
] = "PENDENTE NO PRAZO"
df_final.loc[
    (
        df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"]
        == "RECURSO PENDENTE"
    )
    &
    (
        data_corte_analise
        > df_final["DATA_LIMITE_PAGAMENTO_RECURSO"]
    ),
    "STATUS_RECURSO_PENDENTE"
] = "PENDENTE VENCIDO"
print("Situação dos recursos pendentes:")

print(
    df_final.loc[
        df_final["STATUS_PRAZO_PAGAMENTO_RECURSO"]
        == "RECURSO PENDENTE",
        "STATUS_RECURSO_PENDENTE"
    ].value_counts()
)
df_final["DIAS_VENCIDO_RECURSO_PENDENTE"] = 0
df_final.loc[
    df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO",
    "DIAS_VENCIDO_RECURSO_PENDENTE"
] = (
    data_corte_analise
    - df_final.loc[
        df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO",
        "DATA_LIMITE_PAGAMENTO_RECURSO"
    ]
).dt.days

#Risco financeiro dos recursos vencidos.
valor_recursos_pendentes_vencidos = df_final.loc[
    df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO",
    "VALOR_RECURSADO"
].sum()

print("Valor dos recursos pendentes vencidos:")
print(round(valor_recursos_pendentes_vencidos, 2))

#quantos dias em média estão vencidos?
media_dias_vencidos_recurso = df_final.loc[
    df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO",
    "DIAS_VENCIDO_RECURSO_PENDENTE"
].mean()

print("Média de dias vencidos dos recursos pendentes:")
print(round(media_dias_vencidos_recurso, 2), "dias")
maior_atraso_recurso_pendente = df_final.loc[
    df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO",
    "DIAS_VENCIDO_RECURSO_PENDENTE"
].max()

print("Maior atraso entre os recursos pendentes:")
print(maior_atraso_recurso_pendente, "dias")

#Aging dos recursos vencidos
df_final["FAIXA_AGING_RECURSO"] = pd.cut(
    df_final["DIAS_VENCIDO_RECURSO_PENDENTE"],
    bins=[0, 15, 30, 60, 90, float("inf")],
    labels=[
        "01-15 DIAS",
        "16-30 DIAS",
        "31-60 DIAS",
        "61-90 DIAS",
        "ACIMA DE 90 DIAS"
    ],
    include_lowest=True
)
aging_recursos = (
    df_final[
        df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO"
    ]
    .groupby(
        "FAIXA_AGING_RECURSO",
        observed=True
    )
    .agg(
        QUANTIDADE=("NR_GUIA", "count"),
        VALOR_RECURSADO=("VALOR_RECURSADO", "sum")
    )
)

print("Aging dos recursos pendentes:")
print(aging_recursos.round(2))
aging_recursos["PERCENTUAL_VALOR"] = (
    aging_recursos["VALOR_RECURSADO"]
    / valor_recursos_pendentes_vencidos
) * 100

print("Aging dos recursos pendentes com percentual:")
print(aging_recursos.round(2))

#Vencidos por convênio
recursos_vencidos_convenio = (
    df_final[
        df_final["STATUS_RECURSO_PENDENTE"] == "PENDENTE VENCIDO"
    ]
    .groupby("NM_CONVENIO_PADRAO")
    .agg(
        QUANTIDADE=("NR_GUIA", "count"),
        VALOR_RECURSADO=("VALOR_RECURSADO", "sum"),
        ATRASO_MEDIO_DIAS=("DIAS_VENCIDO_RECURSO_PENDENTE", "mean"),
        MAIOR_ATRASO_DIAS=("DIAS_VENCIDO_RECURSO_PENDENTE", "max")
    )
)
recursos_vencidos_convenio["PERCENTUAL_VALOR"] = (
    recursos_vencidos_convenio["VALOR_RECURSADO"]
    / valor_recursos_pendentes_vencidos
) * 100
recursos_vencidos_convenio = (
    recursos_vencidos_convenio
    .sort_values(
        by="VALOR_RECURSADO",
        ascending=False
    )
)
print("Recursos pendentes vencidos por convênio:")
print(recursos_vencidos_convenio.round(2))

#Trazer as regras de glosa para a base final
df_final["GLOSA_NAO_CLASSIFICADA"] = (
    df_final["GLOSA_INICIAL"]
    - df_final["GLOSA_DESCONSIDERADA"]
    - df_final["VALOR_RECURSADO"]
).round(2)

df_final["STATUS_RECURSO"] = "SEM ACOMPANHAMENTO"

tem_acompanhamento = (
    df_final["STATUS_ACOMPANHAMENTO_FINANCEIRO"]
    == "COM ACOMPANHAMENTO"
)

df_final.loc[
    tem_acompanhamento,
    "STATUS_RECURSO"
] = "SEM RECURSO"

df_final.loc[
    tem_acompanhamento
    & (df_final["VALOR_RECURSADO"] > 0),
    "STATUS_RECURSO"
] = "PENDENTE"

df_final.loc[
    tem_acompanhamento
    & df_final["DATA_PAGAMENTO_RECURSO"].notna(),
    "STATUS_RECURSO"
] = "FINALIZADO"

#Valor recuperado após recurso
df_final["VALOR_RECUPERADO_RECURSO"] = (
    df_final["VALOR_PAGO_RECURSO"]
)

df_final["RECURSO_PENDENTE"] = 0.0

df_final.loc[
    df_final["STATUS_RECURSO"] == "PENDENTE",
    "RECURSO_PENDENTE"
] = df_final["VALOR_RECURSADO"]

df_final.loc[
    df_final["STATUS_RECURSO"] == "SEM ACOMPANHAMENTO",
    "RECURSO_PENDENTE"
] = float("nan")

df_final["PERDA_RECURSO"] = 0.0

df_final.loc[
    df_final["STATUS_RECURSO"] == "FINALIZADO",
    "PERDA_RECURSO"
] = (
    df_final["VALOR_RECURSADO"]
    - df_final["VALOR_PAGO_RECURSO"]
).round(2)

df_final.loc[
    df_final["STATUS_RECURSO"] == "SEM ACOMPANHAMENTO",
    "PERDA_RECURSO"
] = float("nan")

df_final["PERDA_DEFINITIVA"] = (
    df_final["GLOSA_DESCONSIDERADA"]
    + df_final["PERDA_RECURSO"]
).round(2)

print("Status consolidado dos recursos:")
print(
    df_final["STATUS_RECURSO"]
    .value_counts()
)

print("Glosa inicial:")
print(round(df_final["GLOSA_INICIAL"].sum(), 2))

print("Glosa aceita:")
print(round(df_final["GLOSA_DESCONSIDERADA"].sum(), 2))

print("Glosa não classificada:")
print(round(df_final["GLOSA_NAO_CLASSIFICADA"].sum(), 2))

print("Valor total recursado:")
print(round(df_final["VALOR_RECURSADO"].sum(), 2))

print("Valor recuperado após recurso:")
print(round(df_final["VALOR_RECUPERADO_RECURSO"].sum(), 2))

print("Recurso pendente:")
print(round(df_final["RECURSO_PENDENTE"].sum(), 2))

print("Perda no recurso:")
print(round(df_final["PERDA_RECURSO"].sum(), 2))

print("Perda definitiva:")
print(round(df_final["PERDA_DEFINITIVA"].sum(), 2))




df_final["STATUS_FINANCEIRO"] = df_final["STATUS_MANUAL"].fillna(
    "SEM ACOMPANHAMENTO"
)

#Tem glosa?
df_final["TEM_GLOSA"] = (
    df_final["GLOSA_INICIAL"]
    .fillna(0)
    .apply(
        lambda x: "SIM" if x > 0 else "NAO"
    )
)

#Quantas glosas chegaram a etapa de recurso?
df_final["TEM_RECURSO"] = (
    df_final["VALOR_RECURSADO"]
    .fillna(0)
    .apply(
        lambda x: "SIM" if x > 0 else "NAO"
    )
)

print("Quantidade final de registros:")
print(df_final.shape[0])

print("Quantidade final de colunas:")
print(df_final.shape[1])

print("Guias únicas na base final:")
print(df_final["NR_GUIA"].nunique())

print("Status financeiro:")
print(df_final["STATUS_FINANCEIRO"].value_counts())

print("Possui glosa:")
print(df_final["TEM_GLOSA"].value_counts())

print("Possui recurso:")
print(df_final["TEM_RECURSO"].value_counts())

os.makedirs(
    "data/processed",
    exist_ok=True
)

arquivo_saida = (
    "data/processed/base_analitica_oncologia.csv"
)

df_final.to_csv(
    arquivo_saida,
    index=False,
    encoding="utf-8-sig"
)

print("Base analítica salva com sucesso:")
print(arquivo_saida)
