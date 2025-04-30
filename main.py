
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

HTML_FORM = """
<!doctype html>
<title>Plánovač nakládky</title>
<h1>Parametry kamionu</h1>
<form method=post>
Délka (m): <input name=delka_kamionu type=number step=0.1 value=13.6> &nbsp;
Šířka (m): <input name=sirka_kamionu type=number step=0.1 value=2.5><br><br>

<h2>Typy palet</h2>
<table border=1 cellpadding=5>
<tr><th>Jméno</th><th>Délka (m)</th><th>Šířka (m)</th><th>Váha (kg)</th><th>Počet</th></tr>
{% for i in range(5) %}
<tr>
<td><input name="jmeno{{i}}" value="Typ {{i+1}}"></td>
<td><input name="delka{{i}}" type=number step=0.01 value=1.2></td>
<td><input name="sirka{{i}}" type=number step=0.01 value=0.8></td>
<td><input name="vaha{{i}}" type=number step=1 value=1000></td>
<td><input name="pocet{{i}}" type=number value=0></td>
</tr>
{% endfor %}
</table><br>

Strategie:
<select name=strategie>
  <option value="nejvetsi">Největší plocha první</option>
  <option value="nejmensi">Nejmenší plocha první</option>
  <option value="nejtezsi">Nejtěžší palety první</option>
  <option value="nahodne">Náhodné pořadí</option>
</select><br><br>

<input type=submit value="Vygenerovat plán">
</form>

{% if image %}
<hr>
<h2>Vizualizace:</h2>
<img src="data:image/png;base64,{{image}}" style="max-width:100%;"><br>

{% if nenalozene %}
<h3>❌ Nenaložené palety:</h3>
<ul>
{% for jmeno, pocet in nenalozene.items() %}
<li>{{ jmeno }}: {{ pocet }} ks</li>
{% endfor %}
</ul>
{% else %}
<p>✅ Všechny palety byly naloženy.</p>
{% endif %}
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    image = None
    nenalozene = {}
    if request.method == "POST":
        try:
            sirka = float(request.form["sirka_kamionu"])
            delka = float(request.form["delka_kamionu"])
        except:
            sirka, delka = 2.5, 13.6

        kamion = Kamion(sirka, delka)
        palety = []

        for i in range(5):
            try:
                jmeno = request.form[f"jmeno{i}"]
                d = float(request.form[f"delka{i}"])
                s = float(request.form[f"sirka{i}"])
                v = float(request.form[f"vaha{i}"])
                p = int(request.form[f"pocet{i}"])
                if p > 0:
                    palety.append(Paleta(d, s, p, jmeno, v))
            except:
                continue

        strategie = request.form["strategie"]
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

    return render_template_string(HTML_FORM, image=image, nenalozene=nenalozene)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
