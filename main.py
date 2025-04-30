from flask import Flask, render_template_string, request
import matplotlib.pyplot as plt
import io
import random
import base64

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
    for paleta in palety:
        for _ in range(paleta.pocet):
            misto = najdi_misto(kamion, paleta, umistene)
            if misto:
                umistene.append((*misto, paleta.jmeno))
            else:
                break
    return umistene

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

HTML_FORM = """
<!doctype html>
<title>Plánovač nakládky</title>
<h1>Zadej více typů palet (každý řádek = jméno,délka,šířka,váha,počet)</h1>
<form method=post>
<textarea name=palety rows=8 cols=80>
Typ A,1.2,0.8,1200,31
Typ B,1.3,0.8,3000,2
Typ C,3.45,0.21,4800,1
</textarea><br>
<label>Strategie:</label>
<select name=strategie>
  <option value="nejvetsi">Největší plocha první</option>
  <option value="nejmensi">Nejmenší plocha první</option>
  <option value="nejtezsi">Nejtěžší palety první</option>
  <option value="nahodne">Náhodné pořadí</option>
</select><br>
<input type=submit value="Vygenerovat plán">
</form>
{% if image %}
<hr>
<h2>Vizualizace:</h2>
<img src="data:image/png;base64,{{image}}" style="max-width:100%;">
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    image = None
    if request.method == "POST":
        vstup = request.form["palety"]
        strategie = request.form["strategie"]
        palety = []

        for radek in vstup.strip().splitlines():
            try:
                jmeno, d, s, v, p = [x.strip() for x in radek.split(",")]
                palety.append(Paleta(float(d), float(s), int(p), jmeno, float(v)))
            except:
                continue

        if strategie == "nejvetsi":
            palety.sort(key=lambda p: p.plocha(), reverse=True)
        elif strategie == "nejmensi":
            palety.sort(key=lambda p: p.plocha())
        elif strategie == "nejtezsi":
            palety.sort(key=lambda p: p.vaha, reverse=True)
        elif strategie == "nahodne":
            random.shuffle(palety)

        kamion = Kamion(2.5, 13.6)
        vysledek = naplanuj(kamion, palety)
        image = vykresli_png(kamion, vysledek)

    return render_template_string(HTML_FORM, image=image)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
