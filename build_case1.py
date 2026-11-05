#!/usr/bin/env python3
"""Simulator FMVA — Studi Kasus Excel 1: PT Cahaya Timur (Rp juta).

Mode: unduh workbook (DATASET + MODEL template kosong) -> bangun model di
Google Sheets (90 mnt) -> jawab 10 soal di simulator dari modelmu sendiri.

Semua angka di-derive dari input; assert menjamin neraca balance tiap tahun,
rantai FCFF, dan DCF. Kunci jawaban MCQ dicetak di akhir (JANGAN di-ship).
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

T = 0.22          # pajak
WACC = 0.11
G = 0.025
GROWTH = 0.10
NWC_PCT = 0.18    # AR 15% + Inv 12% - AP 9%
AR_PCT, INV_PCT, AP_PCT = 0.15, 0.12, 0.09
COGS_PCT, OPEX_PCT = 0.61, 0.19
SHARES_JT = 50.0  # juta saham

HIST = {
    2024: dict(rev=120000, cogs=72000, opex=24000, da=6000, interest=2000),
    2025: dict(rev=138000, cogs=84180, opex=26220, da=6900, interest=2200,
               cash=15000, ppe=55200, debt=30000, equity=65040),
}
FC = {
    2026: dict(da=7500, capex=9000),
    2027: dict(da=8000, capex=9500, repay=5000),
    2028: dict(da=8500, capex=10000),
}
YEARS = [2026, 2027, 2028]

def build_model():
    m = {}
    # historical NI/BS pieces needed
    for y in (2024, 2025):
        h = HIST[y]
        ebitda = h["rev"] - h["cogs"] - h["opex"]
        ebit = ebitda - h["da"]
        ebt = ebit - h["interest"]
        ni = ebt * (1 - T)
        m[y] = dict(ebitda=ebitda, ebit=ebit, ni=ni)
    # 2025 BS components (given)
    h25 = HIST[2025]
    ar25, inv25 = h25["rev"] * AR_PCT, h25["rev"] * INV_PCT
    ap25 = h25["rev"] * AP_PCT
    assert abs((h25["cash"] + ar25 + inv25 + h25["ppe"]) - (ap25 + h25["debt"] + h25["equity"])) < 0.01, "BS 2025 tak balance"
    prev = dict(rev=h25["rev"], nwc=h25["rev"] * NWC_PCT, cash=h25["cash"],
                ppe=h25["ppe"], debt=h25["debt"], eq=h25["equity"])
    for y in YEARS:
        rev = prev["rev"] * (1 + GROWTH)
        cogs, opex, da = rev * COGS_PCT, rev * OPEX_PCT, FC[y]["da"]
        ebitda = rev - cogs - opex
        ebit = ebitda - da
        interest = 2000.0
        ebt = ebit - interest
        ni = ebt * (1 - T)
        nopat = ebit * (1 - T)
        nwc = rev * NWC_PCT
        dnwc = nwc - prev["nwc"]
        fcff = nopat + da - FC[y]["capex"] - dnwc
        cfo = ni + da - dnwc
        cfi = -FC[y]["capex"]
        repay = FC[y].get("repay", 0.0)
        cff = -repay
        dcash = cfo + cfi + cff
        cash = prev["cash"] + dcash
        ppe = prev["ppe"] + FC[y]["capex"] - da
        ar, inv, ap = rev * AR_PCT, rev * INV_PCT, rev * AP_PCT
        debt = prev["debt"] - repay
        eq = prev["eq"] + ni
        ta = cash + ar + inv + ppe
        tl = ap + debt
        assert abs(ta - (tl + eq)) < 0.02, f"BS {y} tak balance: {ta} vs {tl+eq}"
        dso = ar / rev * 365
        m[y] = dict(rev=rev, cogs=cogs, opex=opex, ebitda=ebitda, da=da, ebit=ebit,
                    interest=interest, ni=ni, nopat=nopat, nwc=nwc, dnwc=dnwc,
                    fcff=fcff, cfo=cfo, cfi=cfi, cff=cff, dcash=dcash, cash=cash,
                    ppe=ppe, ar=ar, inv=inv, ap=ap, debt=debt, eq=eq, ta=ta, dso=dso)
        prev = dict(rev=rev, nwc=nwc, cash=cash, ppe=ppe, debt=debt, eq=eq)
    # DCF @ end-2025
    pv = sum(m[y]["fcff"] / (1 + WACC) ** (y - 2025) for y in YEARS)
    tv = m[2028]["fcff"] * (1 + G) / (WACC - G)
    pv_tv = tv / (1 + WACC) ** 3
    ev = pv + pv_tv
    netdebt = HIST[2025]["debt"] - HIST[2025]["cash"]
    eqv = ev - netdebt
    pps = eqv / SHARES_JT
    # sensitivity WACC 12%
    w2 = 0.12
    pv2 = sum(m[y]["fcff"] / (1 + w2) ** (y - 2025) for y in YEARS)
    tv2 = m[2028]["fcff"] * (1 + G) / (w2 - G)
    ev2 = pv2 + tv2 / (1 + w2) ** 3
    m["dcf"] = dict(pv=pv, tv=tv, pv_tv=pv_tv, ev=ev, netdebt=netdebt,
                    eqv=eqv, pps=pps, ev_wacc12=ev2)
    return m

TITLEF = Font(bold=True, size=13); HDRF = Font(bold=True, color="FFFFFF")
HDR = PatternFill("solid", fgColor="1F3864"); BLUE = PatternFill("solid", fgColor="DCE6F1")
LBLF = Font(bold=True); thin = Border(*[Side(style="thin")] * 4)
wrap = Alignment(wrap_text=True, vertical="top")
numfmt = '#,##0.00'

def style_header(ws, row, cols=5):
    for c in range(1, cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR; cell.font = HDRF; cell.border = thin

def build_workbook(path, m):
    wb = openpyxl.Workbook()
    # ---------- DATASET ----------
    ws = wb.active; ws.title = "DATASET"
    ws.sheet_properties.tabColor = "1F3864"
    for col, w in zip("ABCDE", (44, 16, 16, 16, 40)):
        ws.column_dimensions[col].width = w
    ws["A1"] = "STUDI KASUS 1 — PT Cahaya Timur (Rp juta) — DATASET"; ws["A1"].font = TITLEF
    ws["A2"] = ("Perusahaan distribusi consumer goods (fiktif). Bangun model forecast 2026–2028 "
                "di sheet MODEL, lalu jawab 10 soal di simulator dari modelmu. "
                "Asumsi di bawah adalah INPUT — jangan diubah.")
    ws["A2"].alignment = wrap; ws.row_dimensions[2].height = 45
    r = 4
    ws.cell(row=r, column=1, value="LAPORAN HISTORIS (aktual)").font = LBLF; r += 1
    hdr = ["Keterangan", "2024", "2025", "", "Catatan"]
    for c, h in enumerate(hdr, 1):
        ws.cell(row=r, column=c, value=h)
    style_header(ws, r); r += 1
    h24, h25 = HIST[2024], HIST[2025]
    rows = [
        ("Pendapatan", h24["rev"], h25["rev"], "", ""),
        ("HPP", -h24["cogs"], -h25["cogs"], "", "2025: 61% pendapatan"),
        ("Beban operasi", -h24["opex"], -h25["opex"], "", "2025: 19% pendapatan"),
        ("Penyusutan (D&A)", -h24["da"], -h25["da"], "", ""),
        ("Beban bunga", -h24["interest"], -h25["interest"], "", "Utang 30.000"),
        ("Kas", "", h25["cash"], "", "Neraca 2025"),
        ("PP&E neto", "", h25["ppe"], "", "Neraca 2025"),
        ("Utang berbunga", "", h25["debt"], "", "Neraca 2025"),
        ("Total ekuitas", "", h25["equity"], "", "Neraca 2025"),
    ]
    for lab, v24, v25, _, note in rows:
        ws.cell(row=r, column=1, value=lab).border = thin
        for c, v in ((2, v24), (3, v25)):
            cell = ws.cell(row=r, column=c, value=v); cell.border = thin
            if isinstance(v, (int, float)): cell.number_format = numfmt
        ws.cell(row=r, column=5, value=note).alignment = wrap
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="ASUMSI FORECAST 2026–2028").font = LBLF; r += 1
    for c, h in enumerate(["Asumsi", "Nilai", "", "", "Keterangan"], 1):
        ws.cell(row=r, column=c, value=h)
    style_header(ws, r); r += 1
    assumptions = [
        ("Pertumbuhan pendapatan", "10% per tahun", "", "", ""),
        ("HPP", "61% dari pendapatan", "", "", ""),
        ("Beban operasi", "19% dari pendapatan", "", "", ""),
        ("D&A", "7.500 / 8.000 / 8.500", "", "", "Jadwal diberikan"),
        ("Capex", "9.000 / 9.500 / 10.000", "", "", ""),
        ("Piutang usaha", "15% dari pendapatan", "", "", ""),
        ("Persediaan", "12% dari pendapatan", "", "", ""),
        ("Utang usaha", "9% dari pendapatan", "", "", ""),
        ("Beban bunga", "2.000 per tahun", "", "", ""),
        ("Pelunasan utang", "5.000 pada 2027", "", "", ""),
        ("Tarif pajak", "22%", "", "", "Tanpa dividen"),
        ("WACC", "11%", "", "", "g terminal 2,5%"),
        ("Saham beredar", "50 juta lembar", "", "", ""),
    ]
    for lab, val, _, _, note in assumptions:
        ws.cell(row=r, column=1, value=lab).border = thin
        ws.cell(row=r, column=2, value=val).border = thin
        ws.cell(row=r, column=5, value=note).alignment = wrap
        r += 1
    # ---------- MODEL (template kosong) ----------
    wm = wb.create_sheet("MODEL")
    wm.sheet_properties.tabColor = "ED7D31"
    for col, w in zip("ABCDE", (36, 16, 16, 16, 34)):
        wm.column_dimensions[col].width = w
    wm["A1"] = "MODEL — isi sel BIRU dengan RUMUS (bukan angka mati)"; wm["A1"].font = TITLEF
    wm["A2"] = ("Bangun: Income Statement → NWC schedule → Balance Sheet (cek balance tiap tahun!) → "
                "Cash Flow → FCFF → DCF. Semua harus nge-link; neraca harus balance.")
    wm["A2"].alignment = wrap; wm.row_dimensions[2].height = 40
    sections = [
        ("INCOME STATEMENT", ["Pendapatan", "HPP", "Laba kotor", "Beban operasi", "EBITDA",
                              "Penyusutan (D&A)", "EBIT", "Beban bunga", "EBT", "Pajak (22%)", "Laba bersih"]),
        ("NWC SCHEDULE", ["Piutang usaha", "Persediaan", "Utang usaha", "NWC", "ΔNWC"]),
        ("BALANCE SHEET", ["Kas", "Piutang usaha", "Persediaan", "PP&E neto", "TOTAL ASET",
                           "Utang usaha", "Utang berbunga", "Total liabilitas", "Total ekuitas",
                           "Cek: A − L − E (harus 0)"]),
        ("CASH FLOW", ["Laba bersih", "+ Penyusutan", "− ΔNWC", "Arus kas operasi (CFO)",
                       "Capex (CFI)", "Pelunasan utang (CFF)", "ΔKas", "Kas akhir"]),
        ("FCFF & DCF", ["NOPAT", "+ Penyusutan", "− Capex", "− ΔNWC", "FCFF",
                        "Terminal value", "Enterprise value (DCF)", "Net debt",
                        "Equity value", "Nilai per saham"]),
    ]
    r = 4
    for title, labels in sections:
        wm.cell(row=r, column=1, value=title).font = Font(bold=True, size=12)
        for c, h in enumerate(["Keterangan", "2026", "2027", "2028", ""], 1):
            wm.cell(row=r + 1, column=c, value=h)
        style_header(wm, r + 1)
        rr = r + 2
        for lab in labels:
            wm.cell(row=rr, column=1, value=lab).border = thin
            if lab.startswith("TOTAL") or lab in ("Laba bersih", "FCFF", "Enterprise value (DCF)",
                                                  "Equity value", "Arus kas operasi (CFO)"):
                wm.cell(row=rr, column=1).font = LBLF
            for c in (2, 3, 4):
                cell = wm.cell(row=rr, column=c); cell.border = thin
                cell.fill = BLUE; cell.number_format = numfmt
            rr += 1
        r = rr + 1
    wb.save(path)
    print("saved", path)

if __name__ == "__main__":
    import os
    m = build_model()
    out = os.path.expanduser("~/workspace/akademi-induk/simulator-fmva")
    os.makedirs(out, exist_ok=True)
    build_workbook(os.path.join(out, "Studi-Kasus-1-PT-Cahaya-Timur.xlsx"), m)
    d = m["dcf"]
    print("\n=== KUNCI (jangan di-ship) ===")
    print(f"rev2026={m[2026]['rev']:,.2f} ebit2026={m[2026]['ebit']:,.2f} cfo2026={m[2026]['cfo']:,.2f}")
    print(f"fcff2027={m[2027]['fcff']:,.2f} nwc2028={m[2028]['nwc']:,.2f} dso2026={m[2026]['dso']:.2f}")
    print(f"EV={d['ev']:,.2f} EqV={d['eqv']:,.2f} pps={d['pps']:,.2f} EV@12%={d['ev_wacc12']:,.2f}")
