# Komandos: b-rollų ir tekstų sudėjimas (APF Kirpėjo skydelis / Premiere)

Vaizdas: `2026-10-01_GRYNIEJI_IR_PALUKANOS`, seka `MONTAZAS`, 25 fps, 1283,80 s (32095 kadrai).

Kintamieji — įklijuok vieną kartą į terminalą:

```bash
SK="$HOME/.claude/skills/apiefinansus-premiere"
AS="$SK/assets"          # cia plano_vartai.py
A="$AS/v3"              # cia destymas.py, dek_brollus.py, dek_tekstus.py, skydelis.py
D="/Volumes/T7 media 2/MONTAVIMUI/10/2026-10-01_GRYNIEJI_IR_PALUKANOS/Pinigai PO RANKA ir 6plaūkanu Claude darbiniai failai"
S=MONTAZAS
```

---

## 0. PIRMA — pamatyti, kur kokie b-rollai ir tekstai turi būti (tik skaito)

```bash
python3 /kelias/iki/apf_ataskaita.py --darbinis "$D" --seka "$S" --csv
```

Išspausdina: plano būseną, kurių ruožų failų nėra, b-rollų vietas (laikas, P-id, inkaras, ką rodyti,
Envato užklausos), ISANKSTINIAI įrašus su „panaudota / PRALEISTA“, kurie b-rollo failai jau atsiųsti
ir kurių nėra, visus tekstus (`esme`) su laikais, V5 infografikų intervalus. Su `--csv` dar įrašo
`ATASKAITA_brollai_MONTAZAS.csv` ir `ATASKAITA_tekstai_MONTAZAS.csv` prie darbinio aplanko.

Nieko nekeičia — gali leisti bet kada.

---

## 1. Kas turi būti padaryta prieš sudėjimą

### 1.1. Penktas ruožas (E05) — **negali būti padarytas komanda**

Montavimas nutrūko ties `E1_MONTAZAS` 4/5 failų. Minčių vienetus (`esme` tekstus, b-rollo laukus)
rašo modelis, ne skriptas, todėl trūkstamo ruožo jokia terminalo komanda nesukurs. Ataskaita (0 punktas)
pasakys, kurio numerio failo nėra.

Ruožų ribos: `0: 0–73,36 | 1: 73,36–381,12 | 2: 381,12–676,64 | 3: 676,64–981,28 | 4: 981,28–1283,80 s`

### 1.2. Dėstymas ir plano vartai

```bash
python3 "$AS/plano_vartai.py" busena --planas "$D/PLANAS.json"              # kas padaryta, kas ne
python3 "$AS/plano_vartai.py" vykdo  --planas "$D/PLANAS.json" --id E06 --seka "$S"   # dėstymas
python3 "$AS/plano_vartai.py" vykdo  --planas "$D/PLANAS.json" --id E07 --seka "$S"   # plano vartai
```

`E06` (`destymas.py`) iš minčių vienetų padaro `V3/planas_V3_MONTAZAS.json` — būtent jis nustato
galutinius b-rollo laikus ir **teksto takelį**:

| Kas po tekstu | Takelis |
|---|---|
| b-rollas | **V13** |
| V5 infografikas | **V12** |
| kamera | **V11** |

Tekstas prasideda ne vieneto pradžioje, o `max(vieneto pradžia, inkaras − pries_inkara_s)`; b-rollai
dedami į **V9**. Tankis: 1–2 b-rollai per pilną turinio minutę. Zonoje **564,36–637,40 s** b-rollų
nededama (ten V3 telefono ekrano įrašas) — tavo nurodymas 2026-10-04.

Po E06 ataskaitos 8 dalis parodys galutinį dėstymą su failais ir takeliais.

---

## 2. Premiere turi būti paruoštas

```bash
python3 "$A/skydelis.py" busena
```

Turi atsakyti, kad Premiere veikia **ir** APF Kirpėjo skydelis įjungtas. Jei parašo
„Premiere veikia (PID …), bet APF Kirpejo skydelis NEIJUNGTAS (CEP motoro nera)“ — atidaryk skydelį
Premiere (Window → Extensions) ir pakartok.

---

## 3. B-ROLLŲ SUDĖJIMAS

```bash
python3 "$AS/plano_vartai.py" vykdo --planas "$D/PLANAS.json" --id E14 --seka "$S"
```

Tai paleidžia tiksliai tą komandą, kuri saugoma plane: pirma per skydelį padaro `MONTAZAS` aktyvia
seka, tada `dek_brollus.py` deda b-rollus į **V9** partijomis po ≤ 40 ir išsaugo projektą.

Jei nori paleisti ranka (tas pats, tik be plano apskaitos — projekto pavadinimą pasitikrink ataskaitos
1 dalyje, laukas `PV`):

```bash
python3 "$A/skydelis.py" skaityk \
  "var q=app.project.sequences,r='nerasta';for(var i=0;i<q.numSequences;i++){if(q[i].name=='$S'){app.project.activeSequence=q[i];r='aktyvi $S';}}r" \
  --reikia "^aktyvi $S$" \
&& python3 "$A/dek_brollus.py" \
  --planas "$D/V3/planas_V3_$S.json" \
  --projektas "<PROJEKTO_VARDAS>.prproj" \
  --seka "$S" \
  --aplankas "$D/BROLL/$S" \
  --jsx-dir "$D/_GEN" \
  --kopijos "/Volumes/T7 media 2/MONTAVIMUI/10/2026-10-01_GRYNIEJI_IR_PALUKANOS/_SENOS_KOPIJOS"
```

Jei dalis b-rollų neatsiųsta, jų sąrašą paduok per `--nerasti <suvestine.json>` — tie bus praleisti,
o tekstai nuo jų perkelti ant kameros arba infografiko (V11/V12).

Po sėkmės logas pasakys: `B-ROLLAI OK: padeta sia karta N` ir padarys kopiją į `_SENOS_KOPIJOS`.

---

## 4. TEKSTŲ SUDĖJIMAS

```bash
python3 "$AS/plano_vartai.py" vykdo --planas "$D/PLANAS.json" --id E15 --seka "$S"
```

`dek_tekstus.py` deda tekstus į V11 / V12 / V13 pagal planą ir išsaugo projektą po **kiekvienos**
partijos (todėl nutrūkus darbas neprapuola).

Ranka:

```bash
python3 "$A/dek_tekstus.py" \
  --planas "$D/V3/planas_V3_$S.json" \
  --projektas "<PROJEKTO_VARDAS>.prproj" \
  --seka "$S"
```

---

## 5. Po sudėjimo

```bash
python3 "$AS/plano_vartai.py" vykdo --planas "$D/PLANAS.json" --id E16 --seka "$S"  # rezultato vartai (18 patikrų)
python3 "$AS/plano_vartai.py" vykdo --planas "$D/PLANAS.json" --id E18               # montavimui.py — medija į Montavimui/
python3 "$AS/plano_vartai.py" busena --planas "$D/PLANAS.json"
```

`E16` patikrina: `NELIESTA, V9=PLANAS, V9-RIBOS, RV-S1, RV-B5, RV-V5, SIULES, SIULES2, RV-TARPAI,
PILNAKADRIAI, V13-BROLL, NEUZDENGTA, TAKELIAI, TEKSTAI=PLANAS, RV-T1, POZICIJOS, AKYS, MD5`.

---

## 6. Žinomos šio vaizdo problemos (rastos prieš nutrūkimą)

| Vieta | Problema |
|---|---|
| 75,08–76,19 s | žodis „Atsiprašau.“ liko sukarpytoje sekoje — karpymo klaida |
| 1093,4–1153,4 s ir 1213,4–1273,4 s | b-rollo vietų nėra (ISANKSTINIAI įrašų neturi) |
| 1009,07 s | parašyta „akcininkė.“, girdisi „akcijų“ |
| 1011,21 s | „tris“ ir „dvi“ — viena klaidinga |
| 1093,84 s | „išnežinojama“ = „iš nežinojimo“ |
| 1213,37–1216,07 s | „800-500 87 eurus“ — turi būti ~8 587 € |
| 1232,29–1233,71 s | „6 300. 33 eurus“, o V5 infografikas Nr. 22 vardinamas `6_332_eurai` — skaičius į ekraną neįdėtas, vietoj jo 4-66 „PERKAMOJI GALIA -37 %“ |
| 1248,59 s | „išvitrui“ — sujaukta |
