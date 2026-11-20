from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

TIME_FMT = "%Y-%m-%dT%H:%M"


def parse_zaman(s: str) -> datetime:
    if not isinstance(s, str) or len(s) != 16:
        raise ValueError(s)
    return datetime.strptime(s, TIME_FMT)


def format_zaman(dt: datetime) -> str:
    return dt.strftime(TIME_FMT)


@dataclass
class KaynakTuru:
    ad: str
    hazirlik_dk: int
    temel_ucret: int
    enerji_yogun: bool
    sertifika: Optional[str]


@dataclass
class Rol:
    ad: str
    haftalik_kota: int
    ileri_gun: int
    azami_sure_dk: int


@dataclass
class Kaynak:
    id: str
    ad: str
    tur: str
    izinli_roller: list[str] = field(default_factory=list)


@dataclass
class Kullanici:
    id: str
    ad: str
    rol: str
    sertifikalar: list[str] = field(default_factory=list)
    bakiye: int = 0
    guvenilirlik: int = 80


@dataclass
class Rezervasyon:
    id: str
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    ucret: int
    durum: str
    paket: Optional[str] = None


@dataclass
class BakimPenceresi:
    kaynak: str
    baslangic: datetime
    bitis: datetime


@dataclass
class BeklemeKaydi:
    id: str
    kullanici: str
    kaynak: str
    baslangic: datetime
    bitis: datetime
    kayit_saati: datetime
