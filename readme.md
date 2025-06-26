# OBSƎRVƎ — Text-Adventure-Engine (Python 3)

Ein kleines Ein-Datei-Projekt, das eine JSON-definierte Welt
( *world.json* ) interpretiert und als klassisches
Schreibmaschinen-Adventure im Terminal ausführt.

---

## Aufrufvarianten

| Befehl  (Shell)                       | Effekt                                                     |
|---------------------------------------|------------------------------------------------------------|
| `python main.py`                      | Startet das Spiel normal mit Tipp-Delay                    |
| `python main.py --debug SCENE_ID`     | Springt direkt in **SCENE_ID**, alle Texte erscheinen sofort |

Das »Debug«-Flag ist praktisch zum »Durchklicken« beim Entwickeln
von Räumen.

---

## Programmstruktur

### 1 .   **CLI-Parsing**

```python
cli = argparse.ArgumentParser()
cli.add_argument("--debug", metavar="SCENE_ID", …)
args = cli.parse_args()
````

* Liest ein optionales Argument `--debug`.
* Setzt anhand dessen den globalen `text_delay`
  – 0 Sekunden im Debug-Modus, sonst 0,04 s.

---

### 2 .   **Hilfsfunktionen**

| Funktion                | Zweck                                                     |
| ----------------------- | --------------------------------------------------------- |
| `clear()`               | Räumt das Terminal plattformspezifisch auf.               |
| `type_text(txt, delay)` | Gibt *txt* mit Schreibmaschinen-Effekt + Trennlinie aus.  |
| `format_action(v, n)`   | Formatiert Menüeinträge zu »Look at …«, »Take …«, …       |
| `stylize(title)`        | Erstellt eine „Glitch“-Überschrift → **> 7H£ £L£V∆70R <** |

---

### 3 .   **Banner & Intro**

* `banner()` zeigt ein ASCII-Logo einmalig.
* `intro()` spielt (falls vorhanden) *intro.json* ab
  und wartet auf **ENTER**.

---

### 4 .   **Welt-Laden**

```python
with open("world.json") as f:
    scenes = json.load(f)["scenes"]
```

*Jede* Scene im JSON ist ein Dict mit:

* `title`, `description`
* optionalen `actions`
* optionalen `items`

---

### 5 .   **Laufende Zustände**

| Variable    | Inhalt                                           |
| ----------- | ------------------------------------------------ |
| `current`   | Aktuelle Scene-ID                                |
| `previous`  | Vorherige Scene-ID (für Titel-Anzeigen)          |
| `inventory` | Dict ← mit Items, die der Spieler trägt          |
| `scene_mem` | Dict \[Scene-ID] → Set freigeschalteter Aktionen |

---

### 6 .   **Haupt-Schleife**

```python
while True:
    scene = scenes[current]
    unlocked = scene_mem[current]
    …
```

1. **Raum Betreten**

   * Titel & Beschreibung nur bei Wechsel anzeigen.

2. **End-Scenes**

   * Wenn `current.startswith("ending_")` → »YOU ESCAPED«/»GAME OVER«.

3. **Menü Bauen**

   * Szene-Aktionen → nur wenn evtl. *requires* erfüllt.
   * Item-Aktionen

     * `take`, `look`, `read`, …
     * `use inv_item on target_item`
   * `"inventory"` wird immer angefügt.

4. **Eingabe Verarbeiten**

   * Zahl → Index ins Menü; sonst freier Text.
   * Parse in `verb`, `noun`, `target`.

5. **Befehlsklassen**

| Klasse                      | Prüf-/Verarbeitungs-Routine                    |
| --------------------------- | ---------------------------------------------- |
| `inventory`                 | Zeigt Inhalt des Spieler-Rucksacks.            |
| **Scene-Action**            | Key in `scene["actions"]`, evtl. *requires*.   |
| **use X on Y**              | Dict unter `items[target]["use"]`.             |
| **take item**               | `items[item]["take"]`, evtl. *requires*.       |
| **Item-Verb** (`look book`) | String **oder** Dict (mit `text`, `gives`, …). |

6. **Mutationen**

* `"gives"`    → Item ins Inventar.
* `"remove"`   → Altes Item verschwindet aus der Szene.
* `"replace"`  → Mehrere Items werden injectet.
* `"broken"`   → Verwendeter Gegenstand wird aus Inventar gelöscht.
* `"once"`     → Aktion nach Benutzung aus JSON entfernt.

---

## Typische JSON-Felder (pro Aktion / Item-Verb)

| Key        | Bedeutung                                                      |
| ---------- | -------------------------------------------------------------- |
| `text`     | Auszugebender Text.                                            |
| `requires` | Aktion *oder* Item, das vorhanden sein muss.                   |
| `gives`    | Item-ID, die ins Inventar gelegt wird.                         |
| `next`     | Ziel-Scene-ID (Raumwechsel / Ende).                            |
| `remove`   | **true** → entfernt das Ziel-Item aus der Szene.               |
| `replace`  | Dict neuer Items, welche die Szene ergänzt.                    |
| `broken`   | Entfernt das benutzte Werkzeug aus dem Inventar.               |
| `once`     | Aktion/Verb wird nach Ausführung aus dem JSON-Objekt entfernt. |

---

## Debug-Workflow

1. `python main.py --debug freezer`
   Überspringt Intro und springt in Szene **freezer**.
2. Typing-Delay ist 0 s → schneller testen.
3. Änderungen an *world.json* erfordern **nur** Neustart, kein Code-Patch.

---

## Erweiterungsideen

* **Automatischer Speichern/Laden** (Serialize `current`, `inventory`, …).
* **Timer-Ereignisse** (z. B. Gasleck explodiert nach X Zügen).
* **Mehrfach-Weltdateien** → CLI-Flag `--world file.json`.
* **Farbausgabe** (mit `colorama`) für Beschreibungen vs. Aktionen.

Viel Spaß beim Basteln!
Bei Fragen / Bugs → Pull-Request oder Issue erstellen.

```
