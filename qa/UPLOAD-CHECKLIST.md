# Simulator upload checker — regression checklist

Wajib dijalankan SEBELUM deploy setiap perubahan grader upload (`checkCaseFile`).
Jalankan di BROWSER SUNGGUHAN (tombol "Periksa Workbook", tanpa timer) — harness Node saja TIDAK cukup
(pelajaran 2026-11-05: harness hanya menangkap apa yang terpikir untuk diuji).

Fixture di `qa/fixtures/` — file Instinct, JANGAN dibuka + save ulang di spreadsheet app
(membuka + save akan recalculate/rewrite dan menghancurkan kasus ujinya).

| # | Fixture / skenario | Harapan |
|---|---|---|
| 1 | `formulas-uncached-3c339332.xlsx` | 0/12, 12× pesan "rumus ada, tapi nilai tersimpan tidak ada", 0× "kosong" |
| 2 | `shared-formulas-26c6dda6.xlsx` (prefix ns0) | 12/12 |
| 3 | `shared-default-ns-175e2ef1.xlsx` (kontrol) | 12/12 |
| 4 | typed-semua (12 sel kunci diketik, nilai benar) | 0/12, 12× "KETIKAN" |
| 5 | campuran 6 rumus + 6 ketik | 6/12 |
| 6 | template kosong | 0/12, 12× "kosong" |
| 7 | satu sel rumus-salah (pps) | 11/12 |

Aturan: skor saja tidak cukup — baca PESAN per sel. "kosong" vs "ketikan" vs
"rumus-tanpa-nilai" adalah tiga keadaan berbeda dan pesannya harus berbeda.
