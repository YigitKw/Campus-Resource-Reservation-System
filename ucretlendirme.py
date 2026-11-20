from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modeller import Rezervasyon, Kaynak

BANTLAR: list[tuple[int, int]] = [
    (8, 10), (10, 12), (12, 14), (14, 16),
    (16, 18), (18, 20), (20, 22),
]


def _bant_indeks(saat: int) -> int:
    return (saat - 8) // 2


def _bant_aralik(bant: tuple[int, int], gun: datetime) -> tuple[datetime, datetime]:
    b = gun.replace(hour=bant[0], minute=0, second=0, microsecond=0)
    e = gun.replace(hour=bant[1], minute=0, second=0, microsecond=0)
    return b, e


def _kesisen_dakika(
    a_bas: datetime, a_bit: datetime,
    b_bas: datetime, b_bit: datetime,
) -> int:
    overlap_start = max(a_bas, b_bas)
    overlap_end = min(a_bit, b_bit)
    if overlap_start >= overlap_end:
        return 0
    return int((overlap_end - overlap_start).total_seconds()) // 60


def doluluk_hesapla(
    tur: str,
    gun: datetime,
    bant: tuple[int, int],
    rezervasyonlar: list[Rezervasyon],
    kaynaklar: list[Kaynak],
) -> float:
    tur_kaynak_idler = {k.id for k in kaynaklar if k.tur == tur}
    tur_kaynak_sayisi = len(tur_kaynak_idler)
    if tur_kaynak_sayisi == 0:
        return 0.0

    bant_bas, bant_bit = _bant_aralik(bant, gun)

    dolu_dk = 0
    for rez in rezervasyonlar:
        if rez.durum not in ("ONAYLI", "KULLANIMDA"):
            continue
        if rez.kaynak not in tur_kaynak_idler:
            continue
        if not (rez.baslangic.date() <= gun.date() <= rez.bitis.date()):
            continue
        dolu_dk += _kesisen_dakika(rez.baslangic, rez.bitis, bant_bas, bant_bit)

    return dolu_dk / (tur_kaynak_sayisi * 120)


def bant_carpani(doluluk: float) -> float:
    if doluluk >= 1.0 - 1e-9:
        return 2.0
    return 1.0 + 0.25 * math.floor(round(4 * doluluk, 9))


def pik_carpani(saat: int, enerji_yogun: bool) -> float:
    if enerji_yogun and 10 <= saat < 16:
        return 1.5
    return 1.0


def ucret_hesapla(
    temel_ucret: int,
    enerji_yogun: bool,
    baslangic: datetime,
    bitis: datetime,
    rezervasyonlar: list[Rezervasyon],
    kaynaklar: list[Kaynak],
    kaynak_turu: str,
) -> int:
    toplam = 0.0
    dilim = baslangic
    delta_15 = timedelta(minutes=15)
    bant_carpan_cache: dict[tuple, float] = {}

    while dilim < bitis:
        gun = dilim
        saat_val = dilim.hour
        bant_idx = _bant_indeks(saat_val)
        anahtar = (gun.date(), bant_idx)

        if anahtar not in bant_carpan_cache:
            bant = BANTLAR[bant_idx]
            d = doluluk_hesapla(kaynak_turu, gun, bant, rezervasyonlar, kaynaklar)
            bant_carpan_cache[anahtar] = bant_carpani(d)

        bc = bant_carpan_cache[anahtar]
        pc = pik_carpani(saat_val, enerji_yogun)

        toplam += temel_ucret * 0.25 * bc * pc
        dilim += delta_15

    return math.floor(toplam + 0.5)
