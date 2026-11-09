#!/usr/bin/env python3
"""QA guard GG-24 — angka yatim / distraktor tak terjelaskan di pembahasan (R9).

Kelas (konsolidasi R9 §6c, GG-24; laporan permukaan Simulator N1):
pembahasan soal (field `e`) menyebut angka yang TIDAK ADA di daftar opsi
(angka yatim — benar secara aritmetika tapi tak terhubung ke opsi mana pun),
dan/atau satu distraktor tidak dijelaskan padahal distraktor lain dijelaskan.

Contoh pemicu (Simulator R9 N1, `CASE_Q` FCFF 2027): pembahasan menyebut
`25.076,48` (NOPAT + D&A - dNWC, lupa capex) yang tidak ada di opsi mana pun,
sementara opsi B `18.308,88` (lupa dNWC) tidak dijelaskan sama sekali.

Jalankan dari root repo:  python3 qa/qa_orphan_numbers.py [index.html]
Exit 0 = ALL PASS. WAJIB ALL PASS sebelum commit/deploy.

Check A (FAIL) — angka yatim:
  Setiap angka "kandidat" di `e` (memuat koma desimal ATAU titik ribuan ATAU
  bilangan bulat >= 100) WAJIB salah satu:
    (1) cocok (dalam toleransi pembulatan opsi) dengan nilai di daftar opsi,
    (2) muncul di teks soal `q` (input soal — bukan angka pembahasan),
    (3) terjangkar lewat rantai derivasi: muncul di segmen yang memuat nilai
        opsi, atau di segmen yang hasilnya adalah nilai yang sudah terjangkar
        (fixpoint — mis. dNWC 2.484 terjangkar lewat segmen kunci, lalu segmen
        "dNWC = 18%x151.800 - 18%x138.000 = 2.484" ikut terjangkar),
    (4) tercantum di ALLOWLIST per-soal di bawah (intermediate yang sudah
        ditriase manusia, dengan alasan).
  Tahun (2000-2099) dan bilangan kecil (< 100, tanpa koma/titik — mis. "1 tahun",
  "4 kuartal", "31 Desember", "20-40%") BUKAN kandidat dan dilewati.
  Angka yang gagal keempat syarat di atas = FAIL, dicetak untuk tinjauan manual.

Check B (WARNING, tidak menggagalkan) — distraktor tak terjelaskan:
  Setiap opsi yang murni numerik (angka + satuan saja, mis. "Rp20.860 juta",
  "66 hari") yang nilainya tidak muncul di `e` dicetak sebagai daftar triase.
  BUKAN fail: di korpus ini sebagian besar distraktor memang tidak dijelaskan
  (penjelasan hanya mengulas kunci + jebakan utama) — memaksakan Check B
  sebagai FAIL berarti menulis ~40 penjelasan distraktor baru, di luar scope
  fix N1. Daftar ini diserahkan ke prompt review ronde berikut (lihat batasan).

Check C (FAIL, pin regresi N1):
  Entri FCFF 2027 WAJIB menjelaskan 18.308,88 dan TIDAK BOLEH memuat 25.076,48.

Batasan (jujur — aturan Septian 9 Nov, jangan pura-pura terkunci):
  1. Guard membandingkan NILAI numerik, bukan besaran bersatuan: "2 triliun"
     vs "2.000 miliar" tidak dikenali sebagai sama. Di korpus ini opsi dan
     pembahasan memakai satuan yang konsisten per soal, jadi tidak ada
     false negative yang diketahui; lintas-satuan tetap butuh mata manusia.
  2. "Intermediate eksplisit" hanya dikenali lewat penjangkaran rantai (aturan
     3) + allowlist. Intermediate kontekstual lintas-soal dalam satu exhibit
     (mis. nilai jawaban soal sebelumnya yang dipakai di soal berikut) TIDAK
     terjangkar otomatis — masuk allowlist dengan alasan (lihat entri 58).
  3. Check B tidak mengunci separuh kelas ("distraktor tak terjelaskan"):
     pola N1 — distraktor yang MERUPAKAN hasil jalur-salah yang dapat dihitung
     dibiarkan sunyi sementara distraktor lain dijelaskan — tidak dapat
     dibedakan guard string dari "distraktor memang tidak dijelaskan".
     Mitigasi: daftar Check B dicetak tiap run + disertakan ke prompt review
     ronde berikut; setiap penjelasan soal BARU wajib menjelaskan semua
     distraktor numeriknya (aturan proses, bukan guard).
  4. Toleransi pencocokan = setengah satuan desimal terakhir opsi
     (mis. opsi "30 hari" cocok dengan "30,4" di pembahasan). Dua opsi yang
     jaraknya < toleransi itu tidak dapat dibedakan guard ini — tidak ada
     kasus seperti itu di korpus saat ini.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "index.html")

ENTRY_RE = re.compile(
    r'\{t:"(?P<t>[^"]*)"(?:,case:(?P<case>[^,}]*)|,(?:exhibit:[A-Z_]+|case:[^,}]*)?)*'
    r',q:"(?P<q>(?:[^"\\]|\\.)*)",o:\[(?P<o>[^\]]*)\],a:(?P<a>\d+),'
    r'e:"(?P<e>(?:[^"\\]|\\.)*)"\}'
)

# Token angka Indonesia: ribuan pakai titik + desimal pakai koma ("25.076,48",
# "151.800", "54,75"), atau desimal pakai titik ("0.18", "1.2" — muncul di kode
# dan sesekali di teks), atau bilangan bulat polos ("500", "365").
TOK_RE = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|\d+\.\d+|\d+")

# (awalan soal, nilai) -> alasan triase manusia. Kunci awalan = 48 karakter
# pertama teks soal — stabil terhadap urutan ulang array.
ALLOWLIST = {
    # "Driver dikali..." — faktor pengali 1,10 (=1+10%) dan 1,05 (=1+5%)
    # dari soal, dan faktor gabungannya 1,155; intermediate eksplisit,
    # bukan kandidat jawaban (tidak ada opsi di dekat nilai-nilai ini).
    ("Proyeksi driver-based: tahun ini 12.000 unit \u00d7 R", 1.1):
        "faktor pengali 1+10% dari soal; intermediate eksplisit",
    ("Proyeksi driver-based: tahun ini 12.000 unit \u00d7 R", 1.05):
        "faktor pengali 1+5% dari soal; intermediate eksplisit",
    ("Proyeksi driver-based: tahun ini 12.000 unit \u00d7 R", 1.155):
        "faktor gabungan 1,10x1,05=1,155; intermediate eksplisit",
    # "FCF Rp100 M tumbuh 10%..." — komponen PV tahun 1-3; jumlahnya + PV-TV
    # = total kunci (1.373,6359 ~= opsi 1.374). Derivasi dijabarkan di `e`.
    ("FCF Rp100 M tumbuh 10%/tahun selama 3 tahun, lal", 98.2143):
        "komponen PV FCF tahun 1; jumlah komponen + PV-TV = total kunci",
    ("FCF Rp100 M tumbuh 10%/tahun selama 3 tahun, lal", 96.4605):
        "komponen PV FCF tahun 2; jumlah komponen + PV-TV = total kunci",
    ("FCF Rp100 M tumbuh 10%/tahun selama 3 tahun, lal", 94.738):
        "komponen PV FCF tahun 3; jumlah komponen + PV-TV = total kunci",
    # "Tawaran Rp550 M..." — nilai antar-metode satu exhibit Maju Jaya
    # (comps 480, precedent 600, net debt 60); 540/28,6%/1,9% intermediate
    # kontekstual yang derivasinya ditunjukkan (600-60=540).
    ("Kasus yang sama \u2014 net debt Rp60 M. Tawaran Rp550", 540.0):
        "ekuitas precedent-implied 600-60; intermediate kontekstual exhibit",
    ("Kasus yang sama \u2014 net debt Rp60 M. Tawaran Rp550", 28.6):
        "premi precedent-implied (28,6%); intermediate kontekstual exhibit",
    ("Kasus yang sama \u2014 net debt Rp60 M. Tawaran Rp550", 1.9):
        "premi vs precedent-implied (1,9%); intermediate kontekstual exhibit",
    # "Berapa DSO..." — derivasi DPO sebagai koreksi jebakan "33 hari"
    # (53,85 hari dari 13.662/92.598; 151.800 = revenue 2026). Segmen DPO
    # tidak terjangkar rantai (hasilnya bukan opsi) — ditriase di sini.
    ("Berapa DSO (days sales outstanding) 2026?", 53.85):
        "DPO 53,85 hari; derivasi koreksi jebakan 33 hari ditunjukkan",
    ("Berapa DSO (days sales outstanding) 2026?", 13662.0):
        "utang usaha 9%x151.800; input derivasi DPO di atas",
    ("Berapa DSO (days sales outstanding) 2026?", 92598.0):
        "HPP 61%x151.800; input derivasi DPO di atas",
    ("Berapa DSO (days sales outstanding) 2026?", 151800.0):
        "revenue 2026; input DATASET untuk derivasi DPO",
}


def parse_num(tok):
    """'25.076,48' -> 25076.48 ; '151.800' -> 151800.0 ; '54,75' -> 54.75 ;
    '0.18' -> 0.18 ; '500' -> 500.0 . Kembalikan (nilai, jumlah_desimal)."""
    if "," in tok:
        dec = len(tok.split(",")[1])
        return float(tok.replace(".", "").replace(",", ".")), dec
    if "." in tok:
        parts = tok.split(".")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            return float(tok), len(parts[1])  # desimal pakai titik
        return float(tok.replace(".", "")), 0  # titik ribuan
    return float(tok), 0


def nums_in(s):
    out = []
    for m in TOK_RE.finditer(s):
        v, dec = parse_num(m.group(0))
        out.append((m.group(0), v, dec))
    return out


def is_year(tok, v):
    return "," not in tok and "." not in tok and 2000 <= v <= 2099


def is_candidate(tok, v):
    """Angka yatim hanya dicari di antara angka 'kandidat': berkoma desimal,
    bertitik ribuan, atau bilangan bulat >= 100. Bilangan kecil polos
    ('1 tahun', '4 kuartal', '31 Desember', '20-40%') dilewati."""
    if is_year(tok, v):
        return False
    return ("," in tok) or ("." in tok) or v >= 100


def matches(v, opt_val, opt_dec):
    """Cocok bila selisih <= setengah satuan desimal terakhir opsi
    (opsi '30 hari' cocok dgn '30,4'; opsi '54,75' butuh +-0,005)."""
    return abs(v - opt_val) <= 0.5 * 10 ** (-opt_dec) + 1e-9


def opt_values(o_str):
    """Semua nilai numerik di daftar opsi (untuk penjangkaran Check A):
    termasuk opsi teks ('Naik dari 2.000 ke 2.400' -> 2000, 2400) dan
    opsi rentang ('Rp480-600 M' -> 480, 600)."""
    vals = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', o_str):
        for _tok, v, dec in nums_in(m.group(1)):
            vals.append((v, dec))
    return vals


def opt_pure_numeric(o_str):
    """Opsi yang MURNI numerik (angka + satuan saja) — yang wajib dijelaskan
    menurut Check B. Opsi teks ('Diskon 10%', 'Naik dari...') dilewati."""
    res = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', o_str):
        t = m.group(1)
        core = t.replace("Rp", "").strip()
        core = core.replace("\u2248", "").strip()  # hapus '≈'
        core = re.sub(r"\s*(Rp/saham|juta|jt|miliar|triliun|M|%|hari)\s*$", "", core)
        core = core.replace("\u2013", "-")  # en-dash rentang
        if re.fullmatch(r"[\d.,]+(?:-[\d.,]+)?", core):
            for _tok, v, dec in nums_in(core):
                res.append((t, v, dec))
    return res


def split_segments(e):
    """Pecah pembahasan jadi segmen kalimat: pemisah ';' atau '.' + spasi.
    Titik di dalam angka ribuan ('151.800') tidak diikuti spasi — aman."""
    parts = []
    for chunk in e.split(";"):
        parts.extend(re.split(r"\.\s+(?=[A-Z0-9(])|\.\s*$", chunk))
    return [p.strip() for p in parts if p.strip()]


def check_entry(idx, m):
    """Kembalikan (orphans, unexplained) untuk satu entri soal."""
    q, o_str, e = m.group("q"), m.group("o"), m.group("e")
    stem = q[:48]
    ovals = opt_values(o_str)
    qvals = [v for _t, v, _d in nums_in(q) if not is_year(_t, v)]

    def is_opt_value(v, dec):
        return any(matches(v, ov, od) for ov, od in ovals)

    segs = split_segments(e)
    # Dua daftar per segmen: SEMUA angka (untuk penjangkaran — nilai opsi
    # seperti "20" atau "80" bukan kandidat tapi tetap menjangkar segmennya)
    # dan angka kandidat saja (yang boleh di-flag sebagai yatim).
    seg_all, seg_cand = [], []
    for s in segs:
        all_ns = nums_in(s)
        seg_all.append(all_ns)
        seg_cand.append([(tok, v, dec) for tok, v, dec in all_ns
                         if is_candidate(tok, v)])
    def seg_result_values(s):
        """Angka sesudah '=' TERAKHIR di segmen (hasil persamaan itu).
        Segmen tanpa '=' -> []."""
        if "=" not in s:
            return []
        tail = s.rsplit("=", 1)[1]
        return [v for _t, v, _d in nums_in(tail)]

    # Fixpoint penjangkaran (HASIL saja yang merambat — bukan operan):
    # segmen terjangkar bila memuat nilai opsi, ATAU bila HASIL persamaannya
    # adalah nilai yang sudah diterima. Benih = nilai opsi + nilai soal.
    # Nilai di segmen terjangkar ikut diterima, sehingga rantai derivasi
    # ("... = 2.484" lalu "dNWC = 18%x151.800 - 18%x138.000 = 2.484")
    # terjangkar transitif. Operan yang berulang (mis. D&A 8.000 yang juga
    # muncul di persamaan yatim) TIDAK menjangkar segmen baru — itulah yang
    # membuat persamaan yatim N1 ("... = 25.076,48") tetap tertangkap meski
    # operannya sudah diterima lewat segmen CFO.
    accepted = set(round(v, 6) for v, _d in ovals)
    for v in qvals:
        accepted.add(round(v, 6))
    for (stem_key, val) in ALLOWLIST:
        if stem_key == stem:
            accepted.add(round(val, 6))
    seg_ok = [False] * len(segs)
    changed = True
    while changed:
        changed = False
        for i, (s, all_ns) in enumerate(zip(segs, seg_all)):
            if seg_ok[i]:
                continue
            has_opt = any(is_opt_value(v, dec) for _t, v, dec in all_ns)
            res_ok = any(round(v, 6) in accepted
                         for v in seg_result_values(s))
            if has_opt or res_ok:
                seg_ok[i] = True
                changed = True
                for _t, v, _d in all_ns:
                    accepted.add(round(v, 6))
    orphans = []
    for i, ns in enumerate(seg_cand):
        if seg_ok[i]:
            continue
        s = segs[i]
        for tok, v, _dec in ns:
            if round(v, 6) in accepted:
                continue
            orphans.append((tok, v, s[:100]))

    # Check B: opsi murni numerik yang nilainya tak muncul di `e`.
    e_vals = [(v, dec) for _t, v, dec in nums_in(e)]
    unexplained = []
    seen = set()
    for raw, v, dec in opt_pure_numeric(o_str):
        if (raw, v) in seen:
            continue
        seen.add((raw, v))
        if not any(matches(v, ev, ed) for ev, ed in e_vals):
            unexplained.append((raw, v))
    return orphans, unexplained


def main():
    src = open(TARGET, encoding="utf-8").read()
    entries = list(ENTRY_RE.finditer(src))
    fails, warns = [], []
    print(f"GG-24 scan: {len(entries)} entri soal di {TARGET}")
    if len(entries) != 70:
        fails.append(f"jumlah entri {len(entries)} != 70 (60 Q + 10 CASE_Q)")
    for idx, m in enumerate(entries):
        orphans, unexplained = check_entry(idx, m)
        for tok, v, seg in orphans:
            fails.append(
                f"[{m.group('t')}] {m.group('q')[:60]!r}: angka yatim "
                f"{tok} (={v:g}) :: {seg}"
            )
        for raw, v in unexplained:
            warns.append(
                f"[{m.group('t')}] {m.group('q')[:60]!r}: distraktor "
                f"tak terjelaskan {raw!r}"
            )
    # Check C — pin regresi N1 (FCFF 2027).
    fcff = [m for m in entries if m.group("q").startswith("Berapa FCFF 2027?")]
    if len(fcff) != 1:
        fails.append(f"entri FCFF 2027 ditemukan {len(fcff)}x (harusnya 1)")
    else:
        e = fcff[0].group("e")
        if "25.076,48" in e or "25076" in e:
            fails.append("PIN N1: angka yatim 25.076,48 muncul kembali di FCFF 2027")
        if "18.308,88" not in e:
            fails.append("PIN N1: penjelasan opsi B 18.308,88 hilang dari FCFF 2027")
    for f in fails:
        print("FAIL " + f)
    for w in warns:
        print("WARN " + w)
    print(f"Check A (angka yatim): {'PASS' if not fails else 'FAIL'} "
          f"— {len(fails)} temuan")
    print(f"Check B (distraktor tak terjelaskan, triase): {len(warns)} item")
    print(f"Check C (pin N1): {'PASS' if not any('PIN N1' in f for f in fails) else 'FAIL'}")
    if fails:
        print("RESULT: FAIL")
        return 1
    print("RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
