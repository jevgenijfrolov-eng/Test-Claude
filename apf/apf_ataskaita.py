#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APF ATASKAITA — kur kokie B-ROLLAI ir kokie TEKSTAI turi buti sudeti.

TIK SKAITO. Nieko nerašo, nekeičia, Premiere nejudina.

Paleidimas (Mac terminale):
    python3 apf_ataskaita.py
    python3 apf_ataskaita.py --darbinis "/kelias/iki/... Claude darbiniai failai" --seka MONTAZAS
    python3 apf_ataskaita.py --csv          # papildomai issaugo du CSV failus prie darbinio aplanko

Ka spausdina:
    1) PLANAS.json busena — kurie zingsniai padaryti, kurie ne
    2) E1_<SEKA>/*.json — kurie ruozai yra, kurio nera
    3) B-ROLLU VIETOS — laikas, P-id, inkaras, ka rodyti, envato uzklausos, serija
    4) ISANKSTINIAI — visi P irasai; pazymi panaudotus ir praleistus
    5) ATSIUSTI B-ROLLAI — kas yra BROLL/<SEKA> aplanke ir ko dar nera
    6) TEKSTAI — laikas, tekstas (esme), spalvos, inkaras
    7) V5 INFOGRAFIKAI — intervalai (nuo ju priklauso teksto takelis)
    8) Jei jau yra planas_V3_<SEKA>.json (po E06) — spausdina GALUTINI destyma:
       b-rollai su failais ir tekstai su takeliais V11/V12/V13
"""

import argparse
import csv
import json
import os
import re
import sys

DEFAULT_DARBINIS = (
    "/Volumes/T7 media 2/MONTAVIMUI/10/2026-10-01_GRYNIEJI_IR_PALUKANOS/"
    "Pinigai PO RANKA ir 6plaūkanu Claude darbiniai failai"
)
DEFAULT_SEKA = "MONTAZAS"

VIDEO_PLETINIAI = (".mp4", ".mov", ".m4v", ".mxf", ".avi", ".mkv", ".webm")


# ---------------------------------------------------------------- pagalbinės

def sk(x):
    """Skaicius arba None."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def laikas(x):
    v = sk(x)
    return "-" if v is None else ("%8.2f" % v)


def ikelk(kelias):
    """Grazina (duomenys, klaida)."""
    if not os.path.isfile(kelias):
        return None, "nera failo"
    try:
        with open(kelias, encoding="utf-8") as f:
            return json.load(f), None
    except ValueError as e:
        return None, "netinkamas JSON: %s" % e
    except OSError as e:
        return None, "nenuskaitomas: %s" % e


def sarasu(d, *raktai):
    """Istraukia sarasa is dict/list bet kurio is paduotu raktu."""
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for r in raktai:
            if isinstance(d.get(r), list):
                return d[r]
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def teksto(x, ilgis=60):
    if x is None:
        return ""
    if isinstance(x, (list, tuple)):
        x = " ".join(str(i) for i in x)
    s = re.sub(r"\s+", " ", str(x)).strip()
    return s if len(s) <= ilgis else s[: ilgis - 1] + "…"


def antraste(t):
    print()
    print("=" * 100)
    print(t)
    print("=" * 100)


def vaizdo_zodziai_tekstu(u):
    vz = u.get("vaizdo_zodziai") or []
    out = []
    for z in vz:
        if isinstance(z, dict):
            w = z.get("w") or z.get("zodis") or ""
            t0 = sk(z.get("t0"))
            out.append("%s@%s" % (w, "%.2f" % t0 if t0 is not None else "?"))
        else:
            out.append(str(z))
    return ", ".join(out)


# ---------------------------------------------------------------- 1. PLANAS

def planas_busena(D):
    antraste("1. PLANAS.json — zingsniu busena")
    P, err = ikelk(os.path.join(D, "PLANAS.json"))
    if err:
        print("  PLANAS.json: %s" % err)
        return None
    par = P.get("parametrai") or {}
    if par:
        print("  parametrai:")
        for k in sorted(par):
            print("    %-18s %s" % (k, teksto(par[k], 160)))
    zing = P.get("zingsniai") or P.get("steps") or {}
    if isinstance(zing, dict):
        eilutes = list(zing.items())
    else:
        eilutes = [((z.get("id"), z.get("seka")), z) for z in zing if isinstance(z, dict)]
    if not eilutes:
        print("  (zingsniu sarasas neatpazintas; raktai: %s)" % ", ".join(sorted(P.keys())))
        return P
    print()
    print("  %-8s %-10s %-26s %s" % ("ID", "SEKA", "REZULTATAS", "PALEIDIMU"))
    print("  " + "-" * 70)
    for k, z in eilutes:
        if not isinstance(z, dict):
            continue
        zid = z.get("id") or (k[0] if isinstance(k, tuple) else k)
        zseka = z.get("seka") or (k[1] if isinstance(k, tuple) else "") or "-"
        rez = z.get("rezultatas") or z.get("busena") or "NEPRADETA"
        pal = z.get("paleidimu") or z.get("paleidimai") or ""
        maxp = z.get("max") or z.get("max_paleidimu") or ""
        print("  %-8s %-10s %-26s %s%s" % (zid, zseka, rez, pal, "/%s" % maxp if maxp else ""))
    return P


# ---------------------------------------------------------------- 2. vienetai

def ikelk_vienetus(D, seka):
    antraste("2. E1_%s — minciu vienetu failai (ruozai)" % seka)
    ap = os.path.join(D, "V3", "E1_%s" % seka)
    if not os.path.isdir(ap):
        print("  nera aplanko: %s" % ap)
        return [], []
    failai = sorted(
        (f for f in os.listdir(ap) if re.match(r"^\d+\.json$", f)),
        key=lambda f: int(f.split(".")[0]),
    )
    print("  aplankas: %s" % ap)
    print("  rasti ruozu failai: %s" % (", ".join(failai) or "(nera)"))

    ruozai, vienetai = [], []
    for f in failai:
        d, err = ikelk(os.path.join(ap, f))
        if err:
            print("  %-10s KLAIDA: %s" % (f, err))
            continue
        vv = sarasu(d, "vienetai", "units")
        t0 = min((sk(u.get("t0")) for u in vv if sk(u.get("t0")) is not None), default=None)
        t1 = max((sk(u.get("t1")) for u in vv if sk(u.get("t1")) is not None), default=None)
        nb = sum(1 for u in vv if str(u.get("vizualizuojama")) in ("1", "True", "true"))
        nt = sum(1 for u in vv if teksto(u.get("esme"), 999))
        print("  %-10s vienetu %-5d b-rollo %-4d su tekstu %-4d ruozas %s – %s s"
              % (f, len(vv), nb, nt, laikas(t0), laikas(t1)))
        ruozai.append(int(f.split(".")[0]))
        for u in vv:
            u["_failas"] = f
        vienetai += vv

    if ruozai:
        truksta = [n for n in range(0, max(ruozai) + 1) if n not in ruozai]
        if truksta:
            print()
            print("  !! TRUKSTA RUOZU: %s  -> E06 (destymas) nepasileis, kol ju nebus"
                  % ", ".join("%d.json" % n for n in truksta))
        else:
            print()
            print("  visi ruozai nuo 0 iki %d yra" % max(ruozai))
    vienetai.sort(key=lambda u: (sk(u.get("t0")) if sk(u.get("t0")) is not None else 0))
    return vienetai, ruozai


# ---------------------------------------------------------- 3. b-rollo vietos

def brollo_vietos(vienetai):
    antraste("3. B-ROLLU VIETOS (vienetai su vizualizuojama=1)")
    v = [u for u in vienetai if str(u.get("vizualizuojama")) in ("1", "True", "true")]
    if not v:
        print("  nera nei vieno vieneto su vizualizuojama=1")
        return v
    print("  is viso: %d" % len(v))
    print()
    print("  %-8s %-9s %-9s %-7s %-4s %-22s %s"
          % ("ID", "NUO s", "IKI s", "P-id", "SER", "INKARAS", "KA RODYTI"))
    print("  " + "-" * 118)
    for u in v:
        print("  %-8s %-9s %-9s %-7s %-4s %-22s %s" % (
            teksto(u.get("id"), 8),
            laikas(u.get("t0")), laikas(u.get("t1")),
            teksto(u.get("isankstinis"), 7) or "-",
            "1" if str(u.get("serija")) in ("1", "True", "true") else "",
            teksto("%s@%s" % (u.get("inkaro_zodis"),
                              "%.2f" % sk(u.get("inkaro_t0")) if sk(u.get("inkaro_t0")) is not None else "?"), 22),
            teksto(u.get("ka_rodyti"), 48),
        ))
    print()
    print("  Envato uzklausos ir vaizdo zodziai:")
    for u in v:
        uz = u.get("envato_uzklausos") or []
        print("    %-8s %-7s vaizdo: %-34s | envato: %s" % (
            teksto(u.get("id"), 8),
            teksto(u.get("isankstinis"), 7) or "-",
            teksto(vaizdo_zodziai_tekstu(u), 34),
            teksto(" / ".join(str(x) for x in uz), 60),
        ))
    nedeti = [u for u in vienetai if str(u.get("brollo_nedeti")) in ("1", "True", "true")]
    if nedeti:
        t0 = min((sk(u.get("t0")) for u in nedeti if sk(u.get("t0")) is not None), default=None)
        t1 = max((sk(u.get("t1")) for u in nedeti if sk(u.get("t1")) is not None), default=None)
        print()
        print("  brollo_nedeti=1 vienetu: %d (zona %s – %s s; ten dengia V3 ekrano irasas)"
              % (len(nedeti), laikas(t0), laikas(t1)))
    return v


# ------------------------------------------------------------ 4. ISANKSTINIAI

def isankstiniai(D, seka, brollo_v):
    antraste("4. ISANKSTINIAI_%s.json — is anksto parinktos vietos" % seka)
    kelias = os.path.join(D, "V3", "ISANKSTINIAI_%s.json" % seka)
    d, err = ikelk(kelias)
    if err:
        print("  %s: %s" % (kelias, err))
        return []
    irasai = sarasu(d, "isankstiniai", "vietos", "irasai", "P")
    print("  failas: %s" % kelias)
    print("  irasu: %d" % len(irasai))
    if irasai and isinstance(irasai[0], dict):
        print("  irasu raktai: %s" % ", ".join(sorted(irasai[0].keys())))
    panaudoti = {str(u.get("isankstinis")) for u in brollo_v if u.get("isankstinis")}
    print()
    print("  %-7s %-5s %-34s %-10s %s" % ("P-id", "SER", "VAIZDO ZODZIAI", "BUSENA", "KA RODYTI"))
    print("  " + "-" * 118)
    praleisti = []
    for r in irasai:
        if not isinstance(r, dict):
            print("  %s" % teksto(r, 100))
            continue
        pid = str(r.get("id") or r.get("P") or r.get("pid") or "?")
        yra = pid in panaudoti
        if not yra:
            praleisti.append(pid)
        print("  %-7s %-5s %-34s %-10s %s" % (
            pid,
            "po" if r.get("serija_po") else "",
            teksto(vaizdo_zodziai_tekstu(r), 34),
            "panaudota" if yra else "PRALEISTA",
            teksto(r.get("ka_rodyti"), 46),
        ))
    if praleisti:
        print()
        print("  PRALEISTI P-id (%d): %s" % (len(praleisti), ", ".join(praleisti)))
    return irasai


# -------------------------------------------------------- 5. atsiusti failai

def atsiusti_brollai(D, seka, irasai, brollo_v):
    antraste("5. ATSIUSTI B-ROLLAI — BROLL/%s aplankas" % seka)
    kandidatai = [
        os.path.join(D, "BROLL", seka),
        os.path.join(D, "BROLL"),
        os.path.join(D, "B-ROLL", seka),
        os.path.join(D, "B-ROLL"),
    ]
    ap = next((k for k in kandidatai if os.path.isdir(k)), None)
    if not ap:
        print("  aplanko nera. Tikrinta:")
        for k in kandidatai:
            print("    %s" % k)
        return {}
    print("  aplankas: %s" % ap)
    failai = []
    for saknis, _, ff in os.walk(ap):
        for f in ff:
            if f.lower().endswith(VIDEO_PLETINIAI):
                p = os.path.join(saknis, f)
                failai.append((f, p, os.path.getsize(p)))
    failai.sort()
    print("  video failu: %d" % len(failai))
    print()
    pagal_id = {}
    for f, p, dydis in failai:
        m = re.match(r"^([A-Z]\d{2,4})", f)
        if m:
            pagal_id.setdefault(m.group(1), []).append(f)
        print("    %-52s %8.1f MB" % (teksto(f, 52), dydis / 1048576.0))

    nori = []
    for r in irasai:
        if isinstance(r, dict):
            pid = str(r.get("id") or r.get("P") or r.get("pid") or "")
            if pid:
                nori.append(pid)
    if nori:
        print()
        print("  Sutapimas su P-id (pagal failo pavadinimo pradzia):")
        for pid in nori:
            got = pagal_id.get(pid)
            print("    %-7s %s" % (pid, ", ".join(got) if got else "— FAILO NERASTA —"))
    return pagal_id


# ---------------------------------------------------------------- 6. tekstai

def tekstai(vienetai):
    antraste("6. TEKSTAI EKRANE (vienetu laukas `esme`)")
    v = [u for u in vienetai if teksto(u.get("esme"), 999)]
    print("  vienetu su tekstu: %d" % len(v))
    print()
    print("  %-8s %-9s %-9s %-22s %-34s %s"
          % ("ID", "NUO s", "IKI s", "INKARAS", "TEKSTAS", "SPALVOS"))
    print("  " + "-" * 118)
    for u in v:
        sp = u.get("esmes_spalvos")
        print("  %-8s %-9s %-9s %-22s %-34s %s" % (
            teksto(u.get("id"), 8),
            laikas(u.get("t0")), laikas(u.get("t1")),
            teksto("%s@%s" % (u.get("inkaro_zodis"),
                              "%.2f" % sk(u.get("inkaro_t0")) if sk(u.get("inkaro_t0")) is not None else "?"), 22),
            teksto(u.get("esme"), 34),
            teksto(sp, 24),
        ))
    print()
    print("  Takelis (V11/V12/V13) NESKAICIUOJAMAS cia — ji nustato destymas.py (E06):")
    print("    * tekstas ant b-rollo            -> V13")
    print("    * tekstas ant V5 infografiko     -> V12")
    print("    * tekstas ant kameros            -> V11")
    print("  Tikslus takelis ir pradzia matomi 8 dalyje, kai jau yra planas_V3_<SEKA>.json.")
    return v


# --------------------------------------------------------- 7. V5 infografikai

def v5_infografikai(D, seka):
    antraste("7. V5 INFOGRAFIKAI — intervalai")
    for failas, raktas in (("ivestys_%s.json" % seka, "V5"), ("V5_zymos_%s.json" % seka, None)):
        kelias = os.path.join(D, "V3", failas)
        d, err = ikelk(kelias)
        if err:
            print("  %-28s %s" % (failas, err))
            continue
        v5 = d.get("V5") if isinstance(d, dict) and "V5" in d else sarasu(d, "zymos", "V5", "infografikai")
        print("  %-28s irasu %d" % (failas, len(v5 or [])))
        if not v5:
            continue
        print("      %-5s %-9s %-9s %s" % ("NR", "NUO s", "IKI s", "PAVADINIMAS"))
        for x in v5:
            if not isinstance(x, dict):
                continue
            print("      %-5s %-9s %-9s %s" % (
                teksto(x.get("nr"), 5),
                laikas(x.get("nuo")), laikas(x.get("iki")),
                teksto(x.get("failas") or x.get("pavadinimas") or x.get("vardas"), 60),
            ))
        return v5
    return []


# ------------------------------------------------------ 8. galutinis destymas

def galutinis_planas(D, seka):
    antraste("8. planas_V3_%s.json — GALUTINIS DESTYMAS (po E06)" % seka)
    kelias = os.path.join(D, "V3", "planas_V3_%s.json" % seka)
    P, err = ikelk(kelias)
    if err:
        print("  %s: %s" % (kelias, err))
        print()
        print("  Reiskia: destymas (E06) dar nepaleistas — galutiniu b-rollo laiku su failais")
        print("  ir tekstu takeliu dar NERA. Juos sukuria E06.")
        return None
    print("  failas: %s" % kelias)
    br = sarasu(P, "brollai", "b_rollai", "broll")
    tx = sarasu(P, "tekstai", "texts")
    print("  b-rollu: %d | tekstu: %d" % (len(br), len(tx)))

    if br:
        print()
        print("  --- B-ROLLAI (deda E14 / dek_brollus.py i takeli V9) ---")
        print("  %-7s %-9s %-9s %-8s %s" % ("ID", "NUO s", "IKI s", "TRUKME", "FAILAS / KA RODYTI"))
        print("  " + "-" * 110)
        for b in br:
            if not isinstance(b, dict):
                continue
            t0, t1 = sk(b.get("nuo")), sk(b.get("iki"))
            print("  %-7s %-9s %-9s %-8s %s" % (
                teksto(b.get("id"), 7), laikas(t0), laikas(t1),
                "%.2f" % (t1 - t0) if (t0 is not None and t1 is not None) else "-",
                teksto(b.get("failas") or b.get("ka_rodyti"), 62),
            ))
    if tx:
        print()
        print("  --- TEKSTAI (deda E15 / dek_tekstus.py) ---")
        print("  %-7s %-7s %-9s %-9s %-12s %s"
              % ("ID", "TAKELIS", "NUO s", "IKI s", "ANT", "TEKSTAS"))
        print("  " + "-" * 110)
        for t in tx:
            if not isinstance(t, dict):
                continue
            print("  %-7s %-7s %-9s %-9s %-12s %s" % (
                teksto(t.get("id"), 7),
                teksto(t.get("takelis"), 7),
                laikas(t.get("nuo")), laikas(t.get("iki")),
                teksto(t.get("ant"), 12),
                teksto(t.get("tekstas") or t.get("esme"), 48),
            ))
    return P


# ------------------------------------------------------------------- CSV

def issaugok_csv(D, seka, brollo_v, tekstu_v):
    b_kelias = os.path.join(D, "ATASKAITA_brollai_%s.csv" % seka)
    t_kelias = os.path.join(D, "ATASKAITA_tekstai_%s.csv" % seka)
    try:
        with open(b_kelias, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "t0", "t1", "isankstinis", "serija", "inkaro_zodis",
                        "inkaro_t0", "vaizdo_zodziai", "ka_rodyti", "envato_uzklausos"])
            for u in brollo_v:
                w.writerow([u.get("id"), u.get("t0"), u.get("t1"), u.get("isankstinis"),
                            u.get("serija"), u.get("inkaro_zodis"), u.get("inkaro_t0"),
                            vaizdo_zodziai_tekstu(u), u.get("ka_rodyti"),
                            " / ".join(str(x) for x in (u.get("envato_uzklausos") or []))])
        with open(t_kelias, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "t0", "t1", "esme", "esmes_spalvos", "inkaro_zodis", "inkaro_t0"])
            for u in tekstu_v:
                w.writerow([u.get("id"), u.get("t0"), u.get("t1"), u.get("esme"),
                            u.get("esmes_spalvos"), u.get("inkaro_zodis"), u.get("inkaro_t0")])
        print()
        print("CSV issaugota:")
        print("  %s" % b_kelias)
        print("  %s" % t_kelias)
    except OSError as e:
        print("CSV neissaugota: %s" % e)


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="APF: kur kokie b-rollai ir tekstai turi buti sudeti (tik skaito)")
    ap.add_argument("--darbinis", default=DEFAULT_DARBINIS, help="Claude darbiniu failu aplankas")
    ap.add_argument("--seka", default=DEFAULT_SEKA, help="sekos vardas (MONTAZAS, VIESAS, ...)")
    ap.add_argument("--csv", action="store_true", help="papildomai issaugoti du CSV failus")
    a = ap.parse_args()

    D, seka = a.darbinis, a.seka
    print("APF ATASKAITA")
    print("darbinis: %s" % D)
    print("seka:     %s" % seka)
    if not os.path.isdir(D):
        print()
        print("STOP: darbinio aplanko nera. Ar prijungtas diskas 'T7 media 2'?")
        return 2

    planas_busena(D)
    vienetai, _ = ikelk_vienetus(D, seka)
    brollo_v = brollo_vietos(vienetai)
    irasai = isankstiniai(D, seka, brollo_v)
    atsiusti_brollai(D, seka, irasai, brollo_v)
    tekstu_v = tekstai(vienetai)
    v5_infografikai(D, seka)
    galutinis_planas(D, seka)

    if a.csv:
        issaugok_csv(D, seka, brollo_v, tekstu_v)

    print()
    print("=" * 100)
    print("Pabaiga. Nieko nepakeista.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
