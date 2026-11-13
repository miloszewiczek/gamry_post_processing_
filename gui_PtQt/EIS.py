import os
import subprocess

class EIS_analysis:
    def __init__(self):
        """Inicjalizacja modułu analizy EIS."""
        print("[INFO] Zainicjalizowano moduł EIS_analysis")

    def run_deareis(self):
        """Uruchamia zewnętrzne oprogramowanie DearEIS w osobnym procesie."""
        sciezka_deareis = "/Users/jakub/.local/bin/deareis"
        try:
            if os.path.exists(sciezka_deareis):
                subprocess.Popen([sciezka_deareis])
            else:
                subprocess.Popen(["uv", "tool", "run", "--python", "3.12", "deareis"])
            print("[INFO] Otwarto program DearEIS pomyślnie.")
        except Exception as e:
            print(f"[BŁĄD] Nie udało się uruchomić DearEIS: {e}")

# Jeśli ten moduł zostanie wywołany bezpośrednio, od razu odpali DearEIS
if __name__ == "__main__":
    analiza = EIS_analysis()
    analiza.run_deareis()