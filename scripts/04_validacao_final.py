import pandas as pd

arquivo = "data/processed/base_analitica_oncologia.csv"

df_validacao = pd.read_csv(
    arquivo,
    encoding="utf-8-sig"
)

print("Quantidade de registros:")
print(df_validacao.shape[0])

print("Quantidade de colunas:")
print(df_validacao.shape[1])

print("Guias únicas:")
print(df_validacao["NR_GUIA"].nunique())

print("Guias duplicadas:")
print(
    df_validacao.duplicated(
        subset=["NR_GUIA"]
    ).sum()
)
print("Faturamento total:")
print(
    round(
        df_validacao["VL_TOTAL_CONTA"].sum(),
        2
    )
)

print("Glosa inicial:")
print(
    round(
        df_validacao["GLOSA_INICIAL"].sum(),
        2
    )
)

print("Valor recursado:")
print(
    round(
        df_validacao["VALOR_RECURSADO"].sum(),
        2
    )
)

print("Perda definitiva:")
print(
    round(
        df_validacao["PERDA_DEFINITIVA"].sum(),
        2
    )
)
