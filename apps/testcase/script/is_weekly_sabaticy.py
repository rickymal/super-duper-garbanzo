#!/usr/bin/env python3
"""
Mostra a lista de semanas sabáticas de um ano e informa
se a semana atual já é sabática ou quando será a próxima.

Autor: você :-)
"""

import datetime as dt
from typing import List, Tuple

def semanas_sabaticas(ano: int) -> List[int]:
    """
    Retorna uma lista com todos os números ISO de semana que
    são sabáticos no ano informado.
    """
    # ISO weeks vão de 1 a 52 ou 53, dependendo do ano
    # Basta pegar as semanas cujo índice (wk-1) % 7 == 6
    total_semanas = dt.date(ano, 12, 28).isocalendar().week  # 52 ou 53
    return [wk for wk in range(1, total_semanas + 1) if (wk - 1) % 7 == 6]

def inicio_fim_da_semana(ano: int, iso_week: int) -> Tuple[dt.date, dt.date]:
    """
    Devolve as datas (segunda, domingo) que delimitam a semana ISO pedida.
    """
    # Segunda-feira
    primeira = dt.date.fromisocalendar(ano, iso_week, 1)
    ultima   = dt.date.fromisocalendar(ano, iso_week, 7)
    return primeira, ultima

def main():
    hoje = dt.date.today()
    ano_atual, semana_atual, _ = hoje.isocalendar()

    sabaticas = semanas_sabaticas(ano_atual)

    print(f"Ano: {ano_atual}")
    print(f"Semana ISO atual: {semana_atual:02d}")
    print()

    if semana_atual in sabaticas:
        ini, fim = inicio_fim_da_semana(ano_atual, semana_atual)
        print("🎉 Você ESTÁ em uma semana sabática!")
        print(f"Ela vai de {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}.")
    else:
        # próxima dentro do mesmo ano ou, se acabou, a 1.ª do próximo ano
        prox = next((wk for wk in sabaticas if wk > semana_atual), None)
        if prox is None:  # já passou a última, então pegue a primeira do ano que vem
            ano_prox = ano_atual + 1
            prox = semanas_sabaticas(ano_prox)[0]
            ano_do_prox = ano_prox
        else:
            ano_do_prox = ano_atual

        ini, fim = inicio_fim_da_semana(ano_do_prox, prox)
        print("❌ Esta não é semana sabática.")
        print(f"A próxima será a ISO {prox:02d}/{ano_do_prox}, de "
              f"{ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}.")

    print("\nSemanas sabáticas do ano:")
    print(", ".join(f"{wk:02d}" for wk in sabaticas))

if __name__ == "__main__":
    main()
