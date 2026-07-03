import originpro as op
import pandas as pd


def create_sheet(df):
    df_flat = df.copy()
    df_flat.columns = [f"Col {i}" for i in range(len(df.columns))]

    # 3. Przygotowanie arkusza w Origin
    op.set_show(True)
    wks = op.new_sheet("w")
    wks.from_df(df_flat)

    # 4. AUTOMATYCZNE PRZENOSZENIE NAZW I WARTOŚCI MULTIINDEXU
    # Iterujemy po wszystkich poziomach indeksu kolumn
    for level_idx, level_name in enumerate(df.columns.names):

        # Pobieramy całą listę wartości dla danego poziomu (np. ['Exp1', 'Exp1', 'Exp2', 'Exp2'])
        level_values = df.columns.get_level_values(level_idx).tolist()

        # Opcja A: Chcesz wrzucić to jako standardowy wiersz metadanych (np. Comments dla poziomu 0, Long Name dla poziomu 1)
        # label_type = 'C' if level_idx == 0 else 'L'
        # wks.set_labels(level_values, label_type)

        # Opcja B (Najlepsza): Tworzymy dedykowany wiersz o nazwie takiej jak w Pandas!
        # Jeśli poziom nie ma nazwy (jest None), dajemy nazwę domyślną
        row_name = level_name if level_name else f"Level_{level_idx}"

        # set_labels ustawia wartości dla CAŁEGO wiersza na raz (nie trzeba pętli po kolumnach!)
        wks.set_labels(level_values, type_=f"{row_name}")