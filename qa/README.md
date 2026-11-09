# QA — Simulator FMVA

| Artefak | Yang dicek | Jalankan |
|---|---|---|
| `qa_orphan_numbers.py` | **GG-24 (R9):** angka yatim / distraktor tak terjelaskan di pembahasan soal (`Q` + `CASE_Q`, 70 entri). Check A FAIL (angka yatim), Check B WARNING triase (distraktor tak terjelaskan), Check C pin regresi N1. WAJIB ALL PASS sebelum commit/deploy. | `python3 qa/qa_orphan_numbers.py` |
| `UPLOAD-CHECKLIST.md` + `fixtures/` | Grader upload (`checkCaseFile`): 7 skenario browser sungguhan dengan fixture Instinct. Wajib sebelum deploy SETIAP perubahan grader — TIDAK diperlukan bila perubahan hanya teks/kunci soal (R9 N1: tidak diperlukan). | Browser sungguhan, lihat checklist |

Aturan kunci (berlaku selalu): `checkCaseFile()` / `single()` byte-identik;
kunci case (EV 192.388,65; pps 3.547,77; TV 211.248,01; FCFF 2026 13.846,80;
12 sel kunci checker) TIDAK BOLEH berubah. Grader upload WAJIB rumus live.
