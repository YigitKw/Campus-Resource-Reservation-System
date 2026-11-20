from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from typing import Any, Optional

from modeller import (
    KaynakTuru, Rol, Kaynak, Kullanici,
    Rezervasyon, BakimPenceresi, BeklemeKaydi,
    parse_zaman, format_zaman,
)
from ucretlendirme import ucret_hesapla


def _id_num(id_str: str) -> int:
    digits = "".join(ch for ch in id_str if ch.isdigit())
    return int(digits) if digits else 0


class RezervasyonMotoru:

    def __init__(self) -> None:
        self.saat: datetime = datetime.min
        self.kaynak_turleri: dict[str, KaynakTuru] = {}
        self.roller: dict[str, Rol] = {}
        self.kaynaklar: dict[str, Kaynak] = {}
        self.kullanicilar: dict[str, Kullanici] = {}
        self.bakim_pencereleri: list[BakimPenceresi] = []
        self.rezervasyonlar: list[Rezervasyon] = []
        self.bekleme_kayitlari: list[BeklemeKaydi] = []
        self._rez_sayac: int = 0
        self._bek_sayac: int = 0
        self._paket_sayac: int = 0

    def yukle(self, dosya_yolu: str) -> None:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            veri = json.load(f)

        self.saat = parse_zaman(veri["saat"])

        for ad, v in veri["kaynak_turleri"].items():
            self.kaynak_turleri[ad] = KaynakTuru(
                ad=ad,
                hazirlik_dk=v["hazirlik_dk"],
                temel_ucret=v["temel_ucret"],
                enerji_yogun=v["enerji_yogun"],
                sertifika=v.get("sertifika"),
            )

        for ad, v in veri["roller"].items():
            self.roller[ad] = Rol(
                ad=ad,
                haftalik_kota=v["haftalik_kota"],
                ileri_gun=v["ileri_gun"],
                azami_sure_dk=v["azami_sure_dk"],
            )

        for k in veri["kaynaklar"]:
            self.kaynaklar[k["id"]] = Kaynak(
                id=k["id"], ad=k["ad"],
                tur=k["tur"],
                izinli_roller=list(k["izinli_roller"]),
            )

        for bp in veri.get("bakim_pencereleri") or []:
            self.bakim_pencereleri.append(BakimPenceresi(
                kaynak=bp["kaynak"],
                baslangic=parse_zaman(bp["baslangic"]),
                bitis=parse_zaman(bp["bitis"]),
            ))

        for u in veri["kullanicilar"]:
            self.kullanicilar[u["id"]] = Kullanici(
                id=u["id"], ad=u["ad"],
                rol=u["rol"],
                sertifikalar=list(u.get("sertifikalar") or []),
                bakiye=u["bakiye"],
                guvenilirlik=u["guvenilirlik"],
            )

    def _kaynak_listesi(self) -> list[Kaynak]:
        return list(self.kaynaklar.values())

    def _dogrula(
        self,
        kullanici_id: str,
        kaynak_id: str,
        baslangic: datetime,
        bitis: datetime,
        skip_bakiye: bool = False,
    ) -> Optional[str]:
        if kullanici_id not in self.kullanicilar:
            return "BULUNAMADI"
        if kaynak_id not in self.kaynaklar:
            return "BULUNAMADI"

        kullanici = self.kullanicilar[kullanici_id]
        kaynak = self.kaynaklar[kaynak_id]
        rol = self.roller[kullanici.rol]
        tur = self.kaynak_turleri[kaynak.tur]

        if baslangic.minute not in (0, 15, 30, 45):
            return "ZAMAN_ADIMI_HATASI"
        if bitis.minute not in (0, 15, 30, 45):
            return "ZAMAN_ADIMI_HATASI"
        if bitis <= baslangic:
            return "ZAMAN_ADIMI_HATASI"

        if baslangic < self.saat:
            return "GECMIS_ZAMAN"

        if baslangic.date() != bitis.date():
            return "CALISMA_SAATI_DISI"
        if baslangic.hour < 8:
            return "CALISMA_SAATI_DISI"
        if bitis.hour > 22 or (bitis.hour == 22 and bitis.minute > 0):
            return "CALISMA_SAATI_DISI"

        sure_dk = int((bitis - baslangic).total_seconds()) // 60
        if sure_dk < 30:
            return "SURE_SINIRI"
        if sure_dk > rol.azami_sure_dk:
            return "SURE_SINIRI"

        ileri_gun = rol.ileri_gun
        if kullanici.guvenilirlik < 50:
            ileri_gun = 1
        sinir = self.saat + timedelta(days=ileri_gun)
        if baslangic > sinir:
            return "ILERI_TARIH_SINIRI"

        if kullanici.rol not in kaynak.izinli_roller:
            return "ROL_IZNI_YOK"

        if tur.sertifika is not None and tur.sertifika not in kullanici.sertifikalar:
            return "SERTIFIKA_YOK"

        for bp in self.bakim_pencereleri:
            if bp.kaynak != kaynak_id:
                continue
            if baslangic < bp.bitis and bitis > bp.baslangic:
                return "BAKIM"

        h = timedelta(minutes=tur.hazirlik_dk)

        kesisme_var = False
        hazirlik_var = False
        ardisik_var = False

        for rez in self.rezervasyonlar:
            if rez.kaynak != kaynak_id:
                continue
            if rez.durum in ("IPTAL", "GELMEDI"):
                continue

            rb = min(rez.baslangic, rez.bitis)
            re = rez.bitis

            if rez.durum in ("ONAYLI", "KULLANIMDA"):
                if baslangic < re and bitis > rb:
                    kesisme_var = True

            if not (baslangic < re and bitis > rb):
                if tur.hazirlik_dk > 0:
                    if baslangic < re + h and bitis + h > rb:
                        hazirlik_var = True

            if rez.kullanici == kullanici_id:
                if not (baslangic < re and bitis > rb):
                    if bitis <= rb:
                        gap = (rb - bitis).total_seconds() / 60
                    else:
                        gap = (baslangic - re).total_seconds() / 60
                    if gap < 60:
                        ardisik_var = True

        if kesisme_var:
            return "KESISME"
        if hazirlik_var:
            return "HAZIRLIK_IHLALI"
        if ardisik_var:
            return "ARDISIK_KULLANIM"

        if not skip_bakiye:
            ucret = self._ucret_hesapla(kaynak, baslangic, bitis)
            if ucret > kullanici.bakiye:
                return "BAKIYE_YETERSIZ"

        return None

    def _ucret_hesapla(
        self,
        kaynak: Kaynak,
        baslangic: datetime,
        bitis: datetime,
    ) -> int:
        tur = self.kaynak_turleri[kaynak.tur]
        return ucret_hesapla(
            temel_ucret=tur.temel_ucret,
            enerji_yogun=tur.enerji_yogun,
            baslangic=baslangic,
            bitis=bitis,
            rezervasyonlar=self.rezervasyonlar,
            kaynaklar=self._kaynak_listesi(),
            kaynak_turu=kaynak.tur,
        )

    def _yeni_rez_id(self) -> str:
        self._rez_sayac += 1
        return f"r{self._rez_sayac}"

    def _yeni_bek_id(self) -> str:
        self._bek_sayac += 1
        return f"b{self._bek_sayac}"

    def _yeni_paket_id(self) -> str:
        self._paket_sayac += 1
        return f"p{self._paket_sayac}"

    def _kullanici_ekle(self, cmd: dict) -> dict:
        uid = cmd.get("id")
        ad = cmd.get("ad")
        if isinstance(uid, str) and uid in self.kullanicilar:
            return {"durum": "RED", "kod": "ID_MEVCUT"}

        rol_ad = cmd.get("rol")
        if not isinstance(rol_ad, str) or rol_ad not in self.roller:
            return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}

        if not isinstance(uid, str) or not uid.strip() or not isinstance(ad, str) or not ad.strip():
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}

        sertifikalar = cmd.get("sertifikalar")
        if sertifikalar is None:
            sertifikalar = []
        if not isinstance(sertifikalar, list) or not all(isinstance(s, str) for s in sertifikalar):
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}

        bakiye = cmd.get("bakiye")
        guvenilirlik = cmd.get("guvenilirlik")
        if not (isinstance(bakiye, int) and not isinstance(bakiye, bool)):
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}
        if not (isinstance(guvenilirlik, int) and not isinstance(guvenilirlik, bool)):
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}
        kota = self.roller[rol_ad].haftalik_kota
        if bakiye < 0 or bakiye > kota:
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}
        if guvenilirlik < 0 or guvenilirlik > 100:
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}

        self.kullanicilar[uid] = Kullanici(
            id=uid,
            ad=ad,
            rol=rol_ad,
            sertifikalar=list(sertifikalar),
            bakiye=bakiye,
            guvenilirlik=guvenilirlik,
        )
        return {"durum": "TAMAM"}

    def _kaynak_ekle(self, cmd: dict) -> dict:
        kid = cmd.get("id")
        ad = cmd.get("ad")
        if isinstance(kid, str) and kid in self.kaynaklar:
            return {"durum": "RED", "kod": "ID_MEVCUT"}

        tur = cmd.get("tur")
        if not isinstance(tur, str) or tur not in self.kaynak_turleri:
            return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}
        izinli_roller = cmd.get("izinli_roller")
        if not isinstance(izinli_roller, list):
            return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}
        for r in izinli_roller:
            if not isinstance(r, str) or r not in self.roller:
                return {"durum": "RED", "kod": "TANIMSIZ_DEGER"}

        if not isinstance(kid, str) or not kid.strip() or not isinstance(ad, str) or not ad.strip():
            return {"durum": "RED", "kod": "GECERSIZ_DEGER"}

        self.kaynaklar[kid] = Kaynak(
            id=kid,
            ad=ad,
            tur=tur,
            izinli_roller=list(izinli_roller),
        )
        return {"durum": "TAMAM"}

    def _rezervasyon(self, cmd: dict) -> dict:
        kullanici_id = cmd.get("kullanici")
        kaynak_id = cmd.get("kaynak")
        if (
            not isinstance(kullanici_id, str)
            or not isinstance(kaynak_id, str)
            or kullanici_id not in self.kullanicilar
            or kaynak_id not in self.kaynaklar
        ):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        try:
            baslangic = parse_zaman(cmd.get("baslangic"))
            bitis = parse_zaman(cmd.get("bitis"))
        except (ValueError, TypeError, KeyError):
            return {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"}

        hata = self._dogrula(kullanici_id, kaynak_id, baslangic, bitis)
        if hata:
            return {"durum": "RED", "kod": hata}

        kaynak = self.kaynaklar[kaynak_id]
        kullanici = self.kullanicilar[kullanici_id]
        ucret = self._ucret_hesapla(kaynak, baslangic, bitis)

        kullanici.bakiye -= ucret

        rez_id = self._yeni_rez_id()
        rez = Rezervasyon(
            id=rez_id,
            kullanici=kullanici_id,
            kaynak=kaynak_id,
            baslangic=baslangic,
            bitis=bitis,
            ucret=ucret,
            durum="ONAYLI",
        )
        self.rezervasyonlar.append(rez)

        return {
            "durum": "TAMAM",
            "rezervasyon_id": rez_id,
            "ucret": ucret,
            "bakiye": kullanici.bakiye,
        }

    def _fiyat(self, cmd: dict) -> dict:
        kullanici_id = cmd.get("kullanici")
        kaynak_id = cmd.get("kaynak")
        if (
            not isinstance(kullanici_id, str)
            or not isinstance(kaynak_id, str)
            or kullanici_id not in self.kullanicilar
            or kaynak_id not in self.kaynaklar
        ):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        try:
            baslangic = parse_zaman(cmd.get("baslangic"))
            bitis = parse_zaman(cmd.get("bitis"))
        except (ValueError, TypeError, KeyError):
            return {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"}

        hata = self._dogrula(kullanici_id, kaynak_id, baslangic, bitis, skip_bakiye=True)
        if hata:
            return {"durum": "RED", "kod": hata}

        kaynak = self.kaynaklar[kaynak_id]
        ucret = self._ucret_hesapla(kaynak, baslangic, bitis)
        return {"durum": "TAMAM", "ucret": ucret}

    def _paket(self, cmd: dict) -> dict:
        kullanici_id = cmd.get("kullanici")
        kalemler = cmd.get("kalemler")

        if not isinstance(kullanici_id, str) or kullanici_id not in self.kullanicilar:
            return {"durum": "RED", "kod": "BULUNAMADI", "kalemler": []}

        if not isinstance(kalemler, list) or len(kalemler) < 2 or len(kalemler) > 4:
            return {"durum": "RED", "kod": "PAKET_BOYUTU", "kalemler": []}

        kullanici = self.kullanicilar[kullanici_id]

        if kullanici.guvenilirlik < 50:
            return {"durum": "RED", "kod": "GUVENILIRLIK_DUSUK", "kalemler": []}

        kalem_sonuclari: list[dict] = []
        kalem_ucretleri: list[int] = []
        herhangi_red = False

        for i, kalem in enumerate(kalemler):
            kaynak_id = kalem.get("kaynak") if isinstance(kalem, dict) else None
            if not isinstance(kaynak_id, str) or kaynak_id not in self.kaynaklar:
                kalem_sonuclari.append({"sira": i, "durum": "RED", "kod": "BULUNAMADI"})
                herhangi_red = True
                kalem_ucretleri.append(0)
                continue

            try:
                bas = parse_zaman(kalem.get("baslangic"))
                bit = parse_zaman(kalem.get("bitis"))
            except (ValueError, TypeError, KeyError):
                kalem_sonuclari.append({"sira": i, "durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"})
                herhangi_red = True
                kalem_ucretleri.append(0)
                continue

            hata = self._dogrula(kullanici_id, kaynak_id, bas, bit, skip_bakiye=True)
            if hata:
                kalem_sonuclari.append({"sira": i, "durum": "RED", "kod": hata})
                herhangi_red = True
                kalem_ucretleri.append(0)
            else:
                kalem_sonuclari.append({"sira": i, "durum": "TAMAM"})
                kaynak = self.kaynaklar[kaynak_id]
                kalem_ucretleri.append(self._ucret_hesapla(kaynak, bas, bit))

        if herhangi_red:
            return {"durum": "RED", "kod": "PAKET_RED", "kalemler": kalem_sonuclari}

        paket_ici_ihlal = False
        for i in range(len(kalemler)):
            for j in range(i + 1, len(kalemler)):
                ki = kalemler[i]
                kj = kalemler[j]
                if ki["kaynak"] != kj["kaynak"]:
                    continue
                bi = parse_zaman(ki["baslangic"])
                ei = parse_zaman(ki["bitis"])
                bj = parse_zaman(kj["baslangic"])
                ej = parse_zaman(kj["bitis"])
                kaynak = self.kaynaklar[ki["kaynak"]]
                tur = self.kaynak_turleri[kaynak.tur]
                h = timedelta(minutes=tur.hazirlik_dk)

                if bi < ej and ei > bj:
                    paket_ici_ihlal = True
                    break

                if tur.hazirlik_dk > 0:
                    if bi < ej + h and ei + h > bj:
                        paket_ici_ihlal = True
                        break

                if ei <= bj:
                    gap = (bj - ei).total_seconds() / 60
                else:
                    gap = (bi - ej).total_seconds() / 60
                if gap < 60:
                    paket_ici_ihlal = True
                    break
            if paket_ici_ihlal:
                break

        if paket_ici_ihlal:
            tamam_kalemler = [{"sira": i, "durum": "TAMAM"} for i in range(len(kalemler))]
            return {"durum": "RED", "kod": "PAKET_ICI_KESISME", "kalemler": tamam_kalemler}

        toplam = sum(kalem_ucretleri)
        if toplam > kullanici.bakiye:
            tamam_kalemler = [{"sira": i, "durum": "TAMAM"} for i in range(len(kalemler))]
            return {"durum": "RED", "kod": "BAKIYE_YETERSIZ", "kalemler": tamam_kalemler}

        paket_id = self._yeni_paket_id()
        rez_idler: list[str] = []

        for i, kalem in enumerate(kalemler):
            kaynak_id = kalem["kaynak"]
            bas = parse_zaman(kalem["baslangic"])
            bit = parse_zaman(kalem["bitis"])

            rez_id = self._yeni_rez_id()
            rez = Rezervasyon(
                id=rez_id,
                kullanici=kullanici_id,
                kaynak=kaynak_id,
                baslangic=bas,
                bitis=bit,
                ucret=kalem_ucretleri[i],
                durum="ONAYLI",
                paket=paket_id,
            )
            self.rezervasyonlar.append(rez)
            rez_idler.append(rez_id)

        kullanici.bakiye -= toplam

        return {
            "durum": "TAMAM",
            "paket_id": paket_id,
            "rezervasyonlar": rez_idler,
            "ucretler": kalem_ucretleri,
            "toplam": toplam,
            "bakiye": kullanici.bakiye,
        }

    def _giris(self, cmd: dict) -> dict:
        rez_id = cmd.get("rezervasyon")
        if not isinstance(rez_id, str):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        rez = self._bul_rez(rez_id)
        if rez is None:
            return {"durum": "RED", "kod": "BULUNAMADI"}

        if rez.durum != "ONAYLI":
            return {"durum": "RED", "kod": "DURUM_HATASI"}

        pencere_bas = rez.baslangic - timedelta(minutes=10)
        pencere_bit = rez.baslangic + timedelta(minutes=15)
        if not (pencere_bas <= self.saat <= pencere_bit):
            return {"durum": "RED", "kod": "GIRIS_PENCERESI_DISI"}

        rez.durum = "KULLANIMDA"
        return {"durum": "TAMAM", "yeni_durum": "KULLANIMDA"}

    def _cikis(self, cmd: dict) -> dict:
        rez_id = cmd.get("rezervasyon")
        if not isinstance(rez_id, str):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        rez = self._bul_rez(rez_id)
        if rez is None:
            return {"durum": "RED", "kod": "BULUNAMADI"}

        if rez.durum != "KULLANIMDA":
            return {"durum": "RED", "kod": "DURUM_HATASI"}

        rez.durum = "TAMAMLANDI"
        rez.bitis = self.saat

        kullanici = self.kullanicilar[rez.kullanici]
        olaylar = self._bekleme_tara(rez.kaynak)

        return {
            "durum": "TAMAM",
            "yeni_durum": "TAMAMLANDI",
            "guvenilirlik": kullanici.guvenilirlik,
            "olaylar": olaylar,
        }

    def _iptal(self, cmd: dict) -> dict:
        rez_id = cmd.get("rezervasyon")
        if not isinstance(rez_id, str):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        rez = self._bul_rez(rez_id)
        if rez is None:
            return {"durum": "RED", "kod": "BULUNAMADI"}

        if rez.durum != "ONAYLI":
            return {"durum": "RED", "kod": "DURUM_HATASI"}

        kullanici = self.kullanicilar[rez.kullanici]
        rol = self.roller[kullanici.rol]

        kalan = (rez.baslangic - self.saat).total_seconds()
        kalan_saat = kalan / 3600

        if kalan_saat >= 24:
            iade_oran = 1.0
            guv_degisim = 0
        elif kalan_saat >= 2:
            iade_oran = 0.5
            guv_degisim = 0
        else:
            iade_oran = 0.0
            guv_degisim = -5

        hesaplanan_iade = math.floor(rez.ucret * iade_oran)

        maks_eklenebilir = max(0, rol.haftalik_kota - kullanici.bakiye)
        gercek_iade = min(hesaplanan_iade, maks_eklenebilir)

        kullanici.bakiye += gercek_iade
        kullanici.guvenilirlik = max(0, min(100, kullanici.guvenilirlik + guv_degisim))
        rez.durum = "IPTAL"

        olaylar = self._bekleme_tara(rez.kaynak)

        return {
            "durum": "TAMAM",
            "iade": gercek_iade,
            "bakiye": kullanici.bakiye,
            "guvenilirlik": kullanici.guvenilirlik,
            "olaylar": olaylar,
        }

    def _bekleme(self, cmd: dict) -> dict:
        kullanici_id = cmd.get("kullanici")
        kaynak_id = cmd.get("kaynak")
        if (
            not isinstance(kullanici_id, str)
            or not isinstance(kaynak_id, str)
            or kullanici_id not in self.kullanicilar
            or kaynak_id not in self.kaynaklar
        ):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        try:
            baslangic = parse_zaman(cmd.get("baslangic"))
            bitis = parse_zaman(cmd.get("bitis"))
        except (ValueError, TypeError, KeyError):
            return {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"}

        hata = self._dogrula(kullanici_id, kaynak_id, baslangic, bitis, skip_bakiye=True)

        if hata is None:
            return {"durum": "RED", "kod": "BEKLEME_GEREKSIZ"}

        if hata not in ("KESISME", "HAZIRLIK_IHLALI"):
            return {"durum": "RED", "kod": hata}

        bek_id = self._yeni_bek_id()
        kayit = BeklemeKaydi(
            id=bek_id,
            kullanici=kullanici_id,
            kaynak=kaynak_id,
            baslangic=baslangic,
            bitis=bitis,
            kayit_saati=self.saat,
        )
        self.bekleme_kayitlari.append(kayit)
        self._bekleme_temizle()
        sira = self._bekleme_sira(kaynak_id, bek_id)

        return {
            "durum": "TAMAM",
            "bekleme_id": bek_id,
            "sira": sira,
        }

    def _sirali_beklemeler(self, kaynak_id: str) -> list[BeklemeKaydi]:
        kaynak_beklemeler = [
            b for b in self.bekleme_kayitlari if b.kaynak == kaynak_id
        ]
        kaynak_beklemeler.sort(key=lambda b: (
            -self.kullanicilar[b.kullanici].guvenilirlik,
            b.kayit_saati,
            _id_num(b.id),
        ))
        return kaynak_beklemeler

    def _bekleme_sira(self, kaynak_id: str, bek_id: str) -> int:
        for i, b in enumerate(self._sirali_beklemeler(kaynak_id)):
            if b.id == bek_id:
                return i + 1
        return -1

    def _bekleme_temizle(self) -> None:
        self.bekleme_kayitlari = [
            b for b in self.bekleme_kayitlari
            if b.baslangic >= self.saat
        ]

    def _bekleme_tara(self, kaynak_id: str) -> list[dict]:
        olaylar: list[dict] = []

        self._bekleme_temizle()

        for bek in self._sirali_beklemeler(kaynak_id):
            if bek not in self.bekleme_kayitlari:
                continue

            hata = self._dogrula(
                bek.kullanici, bek.kaynak, bek.baslangic, bek.bitis,
            )
            if hata is not None:
                continue

            kaynak = self.kaynaklar[bek.kaynak]
            kullanici = self.kullanicilar[bek.kullanici]
            ucret = self._ucret_hesapla(kaynak, bek.baslangic, bek.bitis)

            kullanici.bakiye -= ucret

            rez_id = self._yeni_rez_id()
            rez = Rezervasyon(
                id=rez_id,
                kullanici=bek.kullanici,
                kaynak=bek.kaynak,
                baslangic=bek.baslangic,
                bitis=bek.bitis,
                ucret=ucret,
                durum="ONAYLI",
            )
            self.rezervasyonlar.append(rez)

            olaylar.append({
                "zaman": format_zaman(self.saat),
                "tur": "OTOMATIK_ATAMA",
                "bekleme": bek.id,
                "rezervasyon": rez_id,
                "kullanici": bek.kullanici,
                "ucret": ucret,
                "bakiye": kullanici.bakiye,
            })

            self.bekleme_kayitlari.remove(bek)

        return olaylar

    def _sorgu(self, cmd: dict) -> dict:
        tur = cmd.get("tur")
        sid = cmd.get("id")
        if not isinstance(sid, str):
            return {"durum": "RED", "kod": "BULUNAMADI"}

        if tur == "kullanici":
            return self._sorgu_kullanici(sid)
        elif tur == "kaynak":
            return self._sorgu_kaynak(sid, cmd.get("gun"))
        else:
            return {"durum": "RED", "kod": "BULUNAMADI"}

    def _sorgu_kullanici(self, uid: str) -> dict:
        if uid not in self.kullanicilar:
            return {"durum": "RED", "kod": "BULUNAMADI"}

        kullanici = self.kullanicilar[uid]
        rezler = [
            r for r in self.rezervasyonlar if r.kullanici == uid
        ]
        rezler.sort(key=lambda r: (r.baslangic, _id_num(r.id)))

        rez_listesi = [
            {
                "id": r.id,
                "kaynak": r.kaynak,
                "baslangic": format_zaman(r.baslangic),
                "bitis": format_zaman(r.bitis),
                "durum": r.durum,
                "ucret": r.ucret,
            }
            for r in rezler
        ]

        return {
            "durum": "TAMAM",
            "bakiye": kullanici.bakiye,
            "guvenilirlik": kullanici.guvenilirlik,
            "rezervasyonlar": rez_listesi,
        }

    def _sorgu_kaynak(self, kid: str, gun_str: Any) -> dict:
        if kid not in self.kaynaklar:
            return {"durum": "RED", "kod": "BULUNAMADI"}

        if not isinstance(gun_str, str) or len(gun_str) != 10:
            return {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"}

        try:
            gun = datetime.strptime(gun_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"}

        doluluk_listesi: list[dict] = []

        for r in self.rezervasyonlar:
            if r.kaynak != kid:
                continue
            if r.durum not in ("ONAYLI", "KULLANIMDA"):
                continue
            if not (r.baslangic.date() <= gun <= r.bitis.date()):
                continue
            doluluk_listesi.append({
                "baslangic": format_zaman(r.baslangic),
                "bitis": format_zaman(r.bitis),
                "tur": "REZERVASYON",
                "rezervasyon": r.id,
            })

        for bp in self.bakim_pencereleri:
            if bp.kaynak != kid:
                continue
            if not (bp.baslangic.date() <= gun <= bp.bitis.date()):
                continue
            doluluk_listesi.append({
                "baslangic": format_zaman(bp.baslangic),
                "bitis": format_zaman(bp.bitis),
                "tur": "BAKIM",
            })

        doluluk_listesi.sort(key=lambda x: x["baslangic"])

        return {
            "durum": "TAMAM",
            "doluluk": doluluk_listesi,
        }

    def _saat(self, cmd: dict) -> dict:
        try:
            yeni_saat = parse_zaman(cmd["zaman"])
        except (ValueError, TypeError, KeyError):
            return {"durum": "RED", "kod": "ZAMAN_ADIMI_HATASI"}

        if yeni_saat < self.saat:
            return {"durum": "RED", "kod": "SAAT_GERI"}

        tum_olaylar: list[dict] = []

        while self.saat < yeni_saat:
            suanki_saat = self.saat
            aday_zamanlar: set[datetime] = set()

            gun_farki = (7 - suanki_saat.weekday()) % 7
            if gun_farki == 0:
                gun_farki = 7
            pzt = (suanki_saat + timedelta(days=gun_farki)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            if suanki_saat < pzt <= yeni_saat:
                aday_zamanlar.add(pzt)

            for rez in self.rezervasyonlar:
                if rez.durum == "KULLANIMDA":
                    if suanki_saat < rez.bitis <= yeni_saat:
                        aday_zamanlar.add(rez.bitis)

            for rez in self.rezervasyonlar:
                if rez.durum == "ONAYLI":
                    gelmedi_zamani = rez.baslangic + timedelta(minutes=15)
                    if suanki_saat < gelmedi_zamani <= yeni_saat:
                        aday_zamanlar.add(gelmedi_zamani)

            if not aday_zamanlar:
                break

            hedef_zaman = min(aday_zamanlar)
            self.saat = hedef_zaman

            if (
                hedef_zaman.weekday() == 0
                and hedef_zaman.hour == 0
                and hedef_zaman.minute == 0
            ):
                self._haftalik_sifirlama()
                tum_olaylar.append({
                    "zaman": format_zaman(hedef_zaman),
                    "tur": "HAFTALIK_SIFIRLAMA",
                })

            tamamlananlar = []
            for rez in self.rezervasyonlar:
                if rez.durum == "KULLANIMDA" and rez.bitis == hedef_zaman:
                    tamamlananlar.append(rez)
            tamamlananlar.sort(key=lambda r: _id_num(r.id))

            for rez in tamamlananlar:
                rez.durum = "TAMAMLANDI"
                kullanici = self.kullanicilar[rez.kullanici]
                kullanici.guvenilirlik = min(100, kullanici.guvenilirlik + 2)
                tum_olaylar.append({
                    "zaman": format_zaman(hedef_zaman),
                    "tur": "TAMAMLANDI",
                    "rezervasyon": rez.id,
                    "kullanici": rez.kullanici,
                    "guvenilirlik": kullanici.guvenilirlik,
                })

            gelmeyenler = []
            for rez in self.rezervasyonlar:
                if rez.durum == "ONAYLI":
                    gelmedi_zamani = rez.baslangic + timedelta(minutes=15)
                    if gelmedi_zamani == hedef_zaman:
                        gelmeyenler.append(rez)
            gelmeyenler.sort(key=lambda r: _id_num(r.id))

            for rez in gelmeyenler:
                rez.durum = "GELMEDI"
                kullanici = self.kullanicilar[rez.kullanici]
                kullanici.guvenilirlik = max(0, kullanici.guvenilirlik - 15)
                tum_olaylar.append({
                    "zaman": format_zaman(hedef_zaman),
                    "tur": "GELMEDI",
                    "rezervasyon": rez.id,
                    "kullanici": rez.kullanici,
                    "guvenilirlik": kullanici.guvenilirlik,
                })

            bosalan_kaynaklar: list[str] = []
            for rez in gelmeyenler:
                if rez.kaynak not in bosalan_kaynaklar:
                    bosalan_kaynaklar.append(rez.kaynak)

            for kaynak_id in bosalan_kaynaklar:
                atama_olaylari = self._bekleme_tara(kaynak_id)
                tum_olaylar.extend(atama_olaylari)

        self.saat = yeni_saat
        self._bekleme_temizle()
        return {"durum": "TAMAM", "olaylar": tum_olaylar}

    def _haftalik_sifirlama(self) -> None:
        for kullanici in self.kullanicilar.values():
            rol = self.roller[kullanici.rol]
            kullanici.bakiye = rol.haftalik_kota

    def _bul_rez(self, rez_id: str) -> Optional[Rezervasyon]:
        for r in self.rezervasyonlar:
            if r.id == rez_id:
                return r
        return None

    def komut_isle(self, cmd: dict) -> dict:
        komut = cmd.get("komut")

        isleyiciler: dict[str, Any] = {
            "kullanici_ekle": self._kullanici_ekle,
            "kaynak_ekle": self._kaynak_ekle,
            "rezervasyon": self._rezervasyon,
            "fiyat": self._fiyat,
            "paket": self._paket,
            "giris": self._giris,
            "cikis": self._cikis,
            "iptal": self._iptal,
            "bekleme": self._bekleme,
            "sorgu": self._sorgu,
            "saat": self._saat,
        }

        isleyici = isleyiciler.get(komut)
        if isleyici is None:
            return {"durum": "RED", "kod": "BILINMEYEN_KOMUT"}

        sonuc = isleyici(cmd)
        sonuc["komut"] = komut
        return sonuc
