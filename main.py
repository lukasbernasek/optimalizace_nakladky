
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64
import random

app = Flask(__name__)

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
    nenalozene = {}
    for paleta in palety:
        zbyva = paleta.pocet
        for _ in range(paleta.pocet):
            misto = najdi_misto(kamion, paleta, umistene)
            if misto:
                umistene.append((*misto, paleta.jmeno))
                zbyva -= 1
            else:
                break
        if zbyva > 0:
            nenalozene[paleta.jmeno] = zbyva
    return umistene, nenalozene

def vykresli_png(kamion, umistene):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, kamion.delka)
    ax.set_ylim(0, kamion.sirka)
    ax.set_title("Optimalizace nakládky kamionu")
    ax.set_xlabel("Délka (m)")
    ax.set_ylabel("Šířka (m)")
    ax.set_aspect('equal')
    ax.grid(True)
    for (x, y, d, s, jmeno) in umistene:
        ax.add_patch(plt.Rectangle((x, y), d, s, fill=True, edgecolor='black'))
        ax.text(x + d/2, y + s/2, jmeno, ha='center', va='center', fontsize=6)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route("/", methods=["GET", "POST"])
def index():
    image = None
    nenalozene = {}
    vysledky = False
    strategie = "nejvetsi"
    sirka = 2.5
    delka = 13.6
    palety_data = []

    if request.method == "POST":
        sirka = float(request.form.get("sirka_kamionu", 2.5))
        delka = float(request.form.get("delka_kamionu", 13.6))
        strategie = request.form.get("strategie", "nejvetsi")
        kamion = Kamion(sirka, delka)
        palety = []
        index = 0
        while f"jmeno{index}" in request.form:
            jmeno = request.form.get(f"jmeno{index}")
            try:
                d = float(request.form.get(f"delka{index}"))
                s = float(request.form.get(f"sirka{index}"))
                v = float(request.form.get(f"vaha{index}"))
                p = int(request.form.get(f"pocet{index}"))
                palety_data.append((jmeno, d, s, v, p))
                if p > 0:
                    palety.append(Paleta(d, s, p, jmeno, v))
            except:
                palety_data.append((jmeno, "", "", "", ""))
            index += 1

        if strategie == "nejvetsi":
            palety.sort(key=lambda p: p.plocha(), reverse=True)
        elif strategie == "nejmensi":
            palety.sort(key=lambda p: p.plocha())
        elif strategie == "nejtezsi":
            palety.sort(key=lambda p: p.vaha, reverse=True)
        elif strategie == "nahodne":
            random.shuffle(palety)

        umistene, nenalozene = naplanuj(kamion, palety)
        image = vykresli_png(kamion, umistene)
        vysledky = True
    else:
        # Výchozích 5 prázdných řádků pro GET načtení
        palety_data = [(f"Typ {i+1}", 1.2, 0.8, 1000, 0) for i in range(5)]

    return render_template("index.html", image=image, nenalozene=nenalozene,
                           vysledky=vysledky, palety_data=palety_data,
                           sirka=sirka, delka=delka, strategie=strategie)
