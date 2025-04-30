
from flask import Flask, render_template_string, request, send_file
import matplotlib.pyplot as plt
import io
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
    for paleta in palety:
        for _ in range(paleta.pocet):
            misto = najdi_misto(kamion, paleta, umistene)
            if misto:
                umistene.append((*misto, paleta.jmeno))
            else:
                break
    return umistene

def vykresli(kamion, umistene):
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
    plt.savefig(buf, format='pdf')
    buf.seek(0)
    plt.close(fig)
    return buf

HTML_FORM = """<!doctype html>
<title>Plánovač nakládky</title>
<h1>Zadej parametry palet</h1>
<form method=post>
  <label>Počet palet:</label><input name=pocet type=number value=10><br>
  <label>Délka (m):</label><input name=delka type=number step=0.01 value=1.2><br>
  <label>Šířka (m):</label><input name=sirka type=number step=0.01 value=0.8><br>
  <label>Váha (kg):</label><input name=vaha type=number value=1200><br>
  <label>Jméno typu:</label><input name=jmeno value="Typ A"><br>
  <label>Strategie:</label>
  <select name=strategie>
    <option value="nejvetsi">Největší plocha první</option>
    <option value="nejmensi">Nejmenší plocha první</option>
    <option value="nejtezsi">Nejtěžší palety první</option>
    <option value="nahodne">Náhodné pořadí</option>
  </select><br>
  <input type=submit value="Vygenerovat plán">
</form>"""

from flask import render_template_string

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        delka = float(request.form['delka'])
        sirka = float(request.form['sirka'])
        pocet = int(request.form['pocet'])
        jmeno = request.form['jmeno']
        vaha = float(request.form['vaha'])
        strategie = request.form['strategie']

        kamion = Kamion(2.5, 13.6)
        palety = [Paleta(delka, sirka, pocet, jmeno, vaha)]

        if strategie == "nejvetsi":
            palety.sort(key=lambda p: p.plocha(), reverse=True)
        elif strategie == "nejmensi":
            palety.sort(key=lambda p: p.plocha())
        elif strategie == "nejtezsi":
            palety.sort(key=lambda p: p.vaha, reverse=True)
        elif strategie == "nahodne":
            random.shuffle(palety)

        vysledek = naplanuj(kamion, palety)
        pdf = vykresli(kamion, vysledek)
        return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name='nakladka.pdf')

    return render_template_string(HTML_FORM)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
