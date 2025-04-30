import matplotlib.pyplot as plt
import random

class Kamion:
    def __init__(self, sirka, delka):
        self.sirka = sirka
        self.delka = delka

class Paleta:
    def __init__(self, delka, sirka, pocet, jmeno, vaha):
        self.delka = delka
        self.sirka = sirka
        self.pocet = pocet
        self.jmeno = jmeno
        self.vaha = vaha

    def plocha(self):
        return self.delka * self.sirka

def koliduje(nova, umistene):
    nx1, ny1, nx2, ny2 = nova
    for (x, y, d, s, _) in umistene:
        ox1, oy1, ox2, oy2 = x, y, x + d, y + s
        if not (nx2 <= ox1 or nx1 >= ox2 or ny2 <= oy1 or ny1 >= oy2):
            return True
    return False

def najdi_misto(kamion, paleta, umistene):
    mozna_mista = [(0, 0)]
    for (x, y, d, s, _) in umistene:
        mozna_mista.append((x + d, y))
        mozna_mista.append((x, y + s))

    for (start_x, start_y) in mozna_mista:
        if (start_x + paleta.delka <= kamion.delka and start_y + paleta.sirka <= kamion.sirka):
            nova = (start_x, start_y, start_x + paleta.delka, start_y + paleta.sirka)
            if not koliduje(nova, umistene):
                return (start_x, start_y, paleta.delka, paleta.sirka)
        if (start_x + paleta.sirka <= kamion.delka and start_y + paleta.delka <= kamion.sirka):
            nova = (start_x, start_y, start_x + paleta.sirka, start_y + paleta.delka)
            if not koliduje(nova, umistene):
                return (start_x, start_y, paleta.sirka, paleta.delka)
    return None

def naplanuj(kamion, palety):
    umistene = []
    nenalozene = []

    while True:
        paleta_vlozena = False
        for paleta in palety:
            if paleta.pocet <= 0:
                continue
            misto = najdi_misto(kamion, paleta, umistene)
            if misto:
                umistene.append((*misto, paleta.jmeno))
                paleta.pocet -= 1
                paleta_vlozena = True
        if not paleta_vlozena:
            break

    for paleta in palety:
        if paleta.pocet > 0:
            nenalozene.append((paleta.jmeno, paleta.pocet))

    return umistene, nenalozene

def vykresli(kamion, umistene, nenalozene, uloz_pdf=None):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, kamion.delka)
    ax.set_ylim(0, kamion.sirka)
    ax.add_patch(plt.Rectangle((0, 0), kamion.delka, kamion.sirka, fill=False, linewidth=2))

    for (x, y, d, s, jmeno) in umistene:
        ax.add_patch(plt.Rectangle((x, y), d, s, fill=True, edgecolor='black'))
        ax.text(x + d/2, y + s/2, jmeno, ha='center', va='center', fontsize=6)

    ax.set_xlabel("Délka (m)")
    ax.set_ylabel("Šířka (m)")
    ax.set_title("Optimalizace nakládky kamionu")
    ax.set_aspect('equal')
    plt.grid(True)

    if uloz_pdf:
        plt.savefig(uloz_pdf)
        print(f"✅ Plán uložen do '{uloz_pdf}'.")

    plt.close(fig)

def priprav_a_nakresli_variantu(kamion, palety_original, strategie, idx):
    palety = [Paleta(p.delka, p.sirka, p.pocet, p.jmeno, p.vaha) for p in palety_original]

    if strategie == "nejvetsi":
        palety.sort(key=lambda p: p.plocha(), reverse=True)
    elif strategie == "nejmensi":
        palety.sort(key=lambda p: p.plocha())
    elif strategie == "nejtezsi":
        palety.sort(key=lambda p: p.vaha, reverse=True)
    elif strategie == "nahodne":
        random.shuffle(palety)

    umistene, nenalozene = naplanuj(kamion, palety)
    vykresli(kamion, umistene, nenalozene, uloz_pdf=f"nakladka_varianta_{idx}.pdf")

# --- Spuštění ---
if __name__ == "__main__":
    kamion = Kamion(2.5, 13.6)

    palety = [
        Paleta(1.2, 0.8, 31, "Typ A", 1200),
        Paleta(1.3, 0.8, 2, "Typ B", 3000),
        Paleta(3.45, 0.21, 1, "Typ C", 4800),
    ]

    strategie_list = ["nejvetsi", "nejmensi", "nejtezsi", "nahodne"]
    for idx, strategie in enumerate(strategie_list, start=1):
        priprav_a_nakresli_variantu(kamion, palety, strategie, idx)

