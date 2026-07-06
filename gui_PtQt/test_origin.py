import originpro as op
import pandas as pd


def create_book(book_name: str) -> op.WBook:
    op.set_show(True)
    wbk = op.new_book('w', lname = book_name)
    return wbk

def create_sheet(df, workbook:op.WBook, sheet_name="Dane", comment = ''):
    """Tworzy nowy arkusz w określonym skoroszycie Origin.

    :param df: DataFrame z MultiIndexem w kolumnach
    :param sheet_name: Nazwa nowego arkusza
    :param book: Obiekt skoroszytu (op.WBook) lub string z nazwą.
                 Jeśli None, tworzy NOWY skoroszyt.
    """
    df_flat = df.copy()
    df_flat.columns = [f"Col {i}" for i in range(len(df.columns))]

    # 3. Przygotowanie/Wybór skoroszytu i arkusza
    op.set_show(True)

    # Logika zarządzania skoroszytem (Workbook)

    # Tworzenie arkusza (Worksheet) w TYM konkretnym skoroszycie
    wks = workbook.add_sheet(sheet_name)

    wks.from_df(df_flat)

    # 4. AUTOMATYCZNE PRZENOSZENIE NAZW I WARTOŚCI MULTIINDEXU
    for level_idx, level_name in enumerate(df.columns.names):
        level_values = df.columns.get_level_values(level_idx).tolist()
        row_name = level_name if level_name else f"Level_{level_idx}"

        if level_name == 'Parameter':
            row_name = 'L'
            

        wks.set_labels(level_values, type_=f"{row_name}")

    comments_to_set = [comment for i in range(len(df.columns))]
    wks.set_labels(comments_to_set, type_ = 'C')

    return workbook  # Zwracamy obiekt skoroszytu, żeby móc do niego dodawać kolejne sheety