#!/usr/bin/env python3
"""
OBSƎRVƎ – Ein einfacher Text-Adventure-Interpreter
Aufruf-Varianten:
    python main.py              → normales Spiel mit Schreibmaschinen-Effekt
    python main.py --debug ID   → startet direkt in Szene *ID* ohne Verzögerung
"""

import json, os, sys, time, argparse   # Standard-Bibliotheken

# ────────────────────────── Befehlszeilen-Argumente ──────────────────────────
cli = argparse.ArgumentParser()
cli.add_argument("--debug", metavar="SCENE_ID",
                 help="Starte direkt in SCENE_ID und deaktiviere den Typewriter-Delay")
args = cli.parse_args()

# ────────────────────── Hilfsfunktionen & Konstanten ─────────────────────────
text_delay = 0.0 if args.debug else 0.04   # Tippen ohne Verzögerung im Debug-Modus

def clear() -> None:
    """Bildschirm plattformabhängig löschen (Windows ↔️ Unix)."""
    os.system("cls" if os.name == "nt" else "clear")

def type_text(txt: str, delay: float | None = None) -> None:
    """
    Gibt einen Text mit Schreibmaschinen-Effekt aus.
    Nach dem Absatz folgt stets eine Trennlinie.
    """
    if delay is None:
        delay = text_delay
    print()
    for ch in txt:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print("\n" + "-" * 40 + "\n")

def format_action(verb: str, noun: str | None = None) -> str:
    """Formatiert einen Menüeintrag lesbar (Look at … / Take … / Use …)."""
    noun = noun.replace('_', ' ') if noun else ''
    mapping = {"look": f"Look at {noun}",
               "take": f"Take {noun}",
               "use":  f"Use {noun}"}
    return mapping.get(verb, f"{verb.capitalize()} {noun}")

def stylize(title: str) -> str:
    """
    ‚Glitch-Typo‘-Schrift für Szenen-Überschriften.
    Bestimmte Buchstaben werden durch Sonderzeichen ersetzt.
    """
    repl = {'o':'0','O':'0','e':'£','E':'£','t':'7','T':'7',
            's':'$','S':'$','a':'@','A':'∆','i':'!','I':'1','b':'8'}
    return "> " + "".join(repl.get(c, c).upper() for c in title) + " <"

# ───────────────────── Intro-Bildschirm & Vorspann ───────────────────────────
def banner() -> None:
    """ASCII-Logo des Spiels einmalig anzeigen."""
    type_text(r"""
  ____   ____   ____   _____  ______  _____  _    _  _______  ______
 |  _ \ |  _ \ |  _ \ | ____||  ____|| ____|| |  | ||__   __||  ____|
 | |_) || |_) || |_) ||  _|  | |__   |  _|  | |  | |   | |   | |__
 |  _ < |  _ < |  _ < | |___ |  __|  | |___ | |__| |   | |   |  __|
 |_| \_\|_| \_\|_| \_\|_____||_|     |_____||_____/    |_|   |_|
                       [  O B S Ǝ R Ǝ V Ǝ  ]""", 0.002)

def intro() -> None:
    """
    Optionale Einleitungs-Texte aus »intro.json« abspielen.
    Wird übersprungen, falls Datei oder Format fehlt.
    """
    try:
        with open("intro.json") as f:
            for line in json.load(f).get("intro", []):
                type_text(line)
    except Exception:
        pass
    input("(Press ENTER to continue…)")

# ─────────────────── Welt-Datei laden & Grundzustand ─────────────────────────
with open("world.json") as f:
    scenes = json.load(f)["scenes"]       # Enthält alle Räume/Enden/Objekte

# Startszene: Entweder aus --debug oder der *ersten* Scene-ID im JSON
current   = args.debug if args.debug in scenes else next(iter(scenes))
previous  = None                         # Vorherige Scene-ID (für Raumwechsel)
inventory = {}                           # Spieler-Inventar  {item_id: item_obj}
scene_mem = {sid: set() for sid in scenes}   # Bereits durchgeführte Aktionen je Raum

# ───────────────────────── Haupt-Spiel-Schleife ──────────────────────────────
clear(); banner()
if not args.debug:
    intro()

while True:
    scene    = scenes[current]           # Aktuelle Szene-Struktur
    unlocked = scene_mem[current]        # Set mit freigeschalteten Befehlen

    # ── Raum neu betreten ────────────────────────────────────────────────────
    if current != previous:
        clear()
        type_text(stylize(scene["title"]), 0.02)   # Überschrift
        type_text(scene["description"])            # Beschreibung
        previous = current

    # ── Enden behandeln ─────────────────────────────────────────────────────
    if current.startswith("ending_"):
        type_text("YOU ESCAPED!" if "good" in current else "GAME OVER")
        break

    # ── Menüeinträge sammeln ────────────────────────────────────────────────
    menu: list[tuple] = []

    # 1) Szenen-Aktionen (z. B. „press b1“)
    for act, res in scene.get("actions", {}).items():
        # Falls eine Voraussetzung existiert, prüfen (Erinnerung ODER Inventar)
        if isinstance(res, dict) and res.get("requires"):
            need = res["requires"]
            if need not in unlocked and need not in inventory:
                continue
        menu.append((act,))              # („look“,)

    # 2) Objekt-bezogene Befehle
    for item_id, item in scene.get("items", {}).items():

        # 2-a  take <item>
        if item_id not in inventory and "take" in item:
            tdef = item["take"]
            if not (isinstance(tdef, dict) and tdef.get("requires")
                                             and tdef["requires"] not in unlocked):
                menu.append(("take", item_id))

        # 2-b  einfache Verben (look / read / …)
        for verb in item:
            if verb not in ("description", "take", "use"):
                menu.append((verb, item_id))

        # 2-c  use <inv_item> on <target>
        if isinstance(item.get("use"), dict):
            req = item["use"].get("requires")
            if req in inventory:
                menu.append(("use", req, item_id))

    # 3) Inventar-Anzeige
    menu.append(("inventory",))

    # ── Menü ausgeben ───────────────────────────────────────────────────────
    print("Available actions:")
    for i, entry in enumerate(menu, 1):
        if entry[0] == "inventory":
            disp = "inventory"
        elif len(entry) == 1:                 # Szene-Befehl
            disp = entry[0]
        elif len(entry) == 2:                 # Verb + Item
            disp = format_action(*entry)
        else:                                 # use X on Y
            disp = f"Use {entry[1].replace('_',' ')} on {entry[2].replace('_',' ')}"
        print(f"{i}. {disp}")

    # ── Eingabe lesen und ggf. Zahl → Befehl umwandeln ──────────────────────
    sel = input("\nChoose a number or type a command:\n> ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(menu):
        sel = " ".join(menu[int(sel) - 1])    # Menütuple in Text umformen

    parts  = sel.lower().split() + [None, None, None]  # Padding für Index-Zugriffe
    verb   = parts[0] or ''
    noun   = parts[1]
    target = parts[3] if len(parts) > 3 else parts[2]

    # ── Sonderfall: Inventar anzeigen ───────────────────────────────────────
    if verb == "inventory":
        txt = "You are carrying: " + ", ".join(inventory) if inventory else "You carry nothing."
        type_text(txt)
        continue

    # ── Szene-Befehle (look, press b1, …) ───────────────────────────────────
    full_cmd = verb if not noun else f"{verb} {noun}"
    if full_cmd in scene.get("actions", {}):
        action = scene["actions"][full_cmd]

        # Voraussetzung prüfen
        if isinstance(action, dict) and action.get("requires"):
            need = action["requires"]
            if need not in unlocked and need not in inventory:
                type_text("You can’t do that yet."); continue

        unlocked.add(full_cmd)              # Befehl merken
        if isinstance(action, dict) and "gives" in action:
            inventory[action["gives"]] = {} # Belohnungs-Item
        type_text(action["text"] if isinstance(action, dict) else action)

        if isinstance(action, dict) and action.get("once"):
            scene["actions"].pop(full_cmd, None)
        if isinstance(action, dict) and "next" in action:
            current = action["next"]
        continue

    # ── use <inv_item> on <target_item> ─────────────────────────────────────
    if target in scene.get("items", {}):
        udef = scene["items"][target].get(verb)
        if isinstance(udef, dict) and udef.get("requires") == noun and noun in inventory:
            type_text(udef.get("text", "You use it."))

            if "gives" in udef:
                inventory[udef["gives"]] = {}
            if udef.get("broken"):
                inventory.pop(noun, None)
            if udef.get("remove"):
                scene["items"].pop(target, None)
            if "replace" in udef:
                scene["items"].update(udef["replace"])
            if "next" in udef:
                current = udef["next"]
            continue

    # ── take <item> ─────────────────────────────────────────────────────────
    if verb == "take" and noun in scene.get("items", {}):
        tdef = scene["items"][noun]["take"]
        if isinstance(tdef, dict) and tdef.get("requires") and tdef["requires"] not in unlocked:
            type_text("Look at it first."); continue

        type_text(tdef["text"] if isinstance(tdef, dict) else tdef)
        if isinstance(tdef, dict) and "gives" in tdef:
            inventory[tdef["gives"]] = {}
        inventory[noun] = scene["items"][noun]
        scene["items"].pop(noun)
        continue

    # ── einfache Item-Verben (look book, read book, …) ─────────────────────
    if noun in scene.get("items", {}) and verb in scene["items"][noun]:
        item_act = scene["items"][noun][verb]

        # Variante A: reiner String
        if isinstance(item_act, str):
            type_text(item_act)
            unlocked.add(f"{verb} {noun}")
            continue

        # Variante B: Dict ➜ kann „text“, „gives“, „remove“… enthalten
        if isinstance(item_act, dict):
            prereq = item_act.get("requires")
            if prereq and prereq not in unlocked and prereq not in inventory:
                type_text("You can’t do that yet."); continue

            type_text(item_act.get("text", "…"))

            if item_act.get("gives"):
                inventory[item_act["gives"]] = {}
            if item_act.get("remove"):
                scene["items"].pop(noun, None)
            if "replace" in item_act:
                scene["items"].update(item_act["replace"])
            if item_act.get("once"):
                scene["items"][noun].pop(verb, None)

            unlocked.add(f"{verb} {noun}")
            continue

    # ── kein Pfad gefunden ─────────────────────────────────────────────────
    type_text("You can’t do that.")
