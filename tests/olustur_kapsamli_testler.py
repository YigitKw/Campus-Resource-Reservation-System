import json
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent
if str(KOK_DIZIN) not in sys.path:
    sys.path.insert(0, str(KOK_DIZIN))

from motor import RezervasyonMotoru


def uret_testler():
    komutlar = []

    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_u1",
        "ad": "Test Ogrenci 1",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_u2",
        "ad": "Test Ogrenci 2 (Sifir Bakiye)",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 0,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_low",
        "ad": "Test Dusuk Guvenilirlik",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 40
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_lab_user",
        "ad": "Test Lab Sertifikali",
        "rol": "ARASTIRMACI",
        "sertifikalar": ["LAB_GUVENLIK"],
        "bakiye": 300,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_iade_user",
        "ad": "Test Iade Tavani Kullanicisi",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 100
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_tamam_user",
        "ad": "Test Tamamlanma Kullanicisi",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 80
    })

    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_u1",
        "ad": "Cift ID",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 100,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_err1",
        "ad": "Tanimsiz Rol",
        "rol": "UZAYLI",
        "sertifikalar": [],
        "bakiye": 50,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_err2",
        "ad": "Kota Asimi",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 500,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_err3",
        "ad": "Bool Bakiye",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": True,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_err4",
        "ad": "Float Bakiye",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 50.5,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_err5",
        "ad": "Yuksek Guvenilirlik",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 50,
        "guvenilirlik": 150
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_err6",
        "ad": "Bool Guvenilirlik",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 50,
        "guvenilirlik": False
    })

    komutlar.append({
        "komut": "kaynak_ekle",
        "id": "ODA-1",
        "ad": "Cift Kaynak",
        "tur": "ODA",
        "izinli_roller": ["OGRENCI"]
    })
    komutlar.append({
        "komut": "kaynak_ekle",
        "id": "TEST-K1",
        "ad": "Tanimsiz Tur",
        "tur": "ROKET",
        "izinli_roller": ["OGRENCI"]
    })
    komutlar.append({
        "komut": "kaynak_ekle",
        "id": "TEST-K2",
        "ad": "Tanimsiz Rol",
        "tur": "ODA",
        "izinli_roller": ["OGRENCI", "ASTRONOT"]
    })
    komutlar.append({
        "komut": "kaynak_ekle",
        "id": "LAB-TEST",
        "ad": "Test Laboratuvari",
        "tur": "LAB",
        "izinli_roller": ["OGRENCI", "ARASTIRMACI", "TEKNISYEN"]
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "olmayan_kullanici",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T10:10",
        "bitis": "2027-03-08T11:00"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T07:10",
        "bitis": "2027-03-08T08:00"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T07:00",
        "bitis": "2027-03-08T07:45"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T22:00",
        "bitis": "2027-03-08T22:15"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-25T10:00",
        "bitis": "2027-03-25T10:15"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "CIH-1",
        "baslangic": "2027-03-25T10:00",
        "bitis": "2027-03-25T11:00"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "CIH-1",
        "baslangic": "2027-03-08T16:30",
        "bitis": "2027-03-08T17:30"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_lab_user",
        "kaynak": "LAB-TEST",
        "baslangic": "2027-03-08T10:00",
        "bitis": "2027-03-08T12:00"
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "LAB-TEST",
        "baslangic": "2027-03-08T10:00",
        "bitis": "2027-03-08T12:00"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "YAZ-2",
        "baslangic": "2027-03-08T09:00",
        "bitis": "2027-03-08T10:30"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_lab_user",
        "kaynak": "LAB-TEST",
        "baslangic": "2027-03-08T11:30",
        "bitis": "2027-03-08T13:00"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_lab_user",
        "kaynak": "LAB-TEST",
        "baslangic": "2027-03-08T12:00",
        "bitis": "2027-03-08T13:00"
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T10:00",
        "bitis": "2027-03-08T11:00"
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T11:30",
        "bitis": "2027-03-08T12:30"
    })

    komutlar.append({
        "komut": "bekleme",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-08T15:00",
        "bitis": "2027-03-08T16:00"
    })

    komutlar.append({
        "komut": "saat",
        "zaman": "2027-03-08T07:00"
    })

    komutlar.append({
        "komut": "paket",
        "kullanici": "t_u1",
        "kalemler": [
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"}
        ]
    })

    komutlar.append({
        "komut": "paket",
        "kullanici": "t_u1",
        "kalemler": [
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"},
            {"kaynak": "ODA-2", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"},
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T12:00", "bitis": "2027-03-09T13:00"},
            {"kaynak": "ODA-2", "baslangic": "2027-03-09T12:00", "bitis": "2027-03-09T13:00"},
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T14:00", "bitis": "2027-03-09T15:00"}
        ]
    })

    komutlar.append({
        "komut": "paket",
        "kullanici": "t_low",
        "kalemler": [
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"},
            {"kaynak": "ODA-2", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"}
        ]
    })

    komutlar.append({
        "komut": "paket",
        "kullanici": "t_u1",
        "kalemler": [
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"},
            {"kaynak": "LAB-TEST", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"}
        ]
    })

    komutlar.append({
        "komut": "paket",
        "kullanici": "t_u1",
        "kalemler": [
            {"kaynak": "ODA-2", "baslangic": "2027-03-09T10:00", "bitis": "2027-03-09T11:00"},
            {"kaynak": "ODA-2", "baslangic": "2027-03-09T11:30", "bitis": "2027-03-09T12:30"}
        ]
    })

    komutlar.append({
        "komut": "paket",
        "kullanici": "t_u2",
        "kalemler": [
            {"kaynak": "ODA-1", "baslangic": "2027-03-09T14:00", "bitis": "2027-03-09T15:00"},
            {"kaynak": "ODA-2", "baslangic": "2027-03-09T14:00", "bitis": "2027-03-09T15:00"}
        ]
    })

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_u1",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-10T14:00",
        "bitis": "2027-03-10T16:00"
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "w_u70_a",
        "ad": "Bekleyen 70A",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 70
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "w_u90_a",
        "ad": "Bekleyen 90A",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 90
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "w_u70_b",
        "ad": "Bekleyen 70B",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 120,
        "guvenilirlik": 70
    })

    komutlar.append({
        "komut": "bekleme",
        "kullanici": "w_u70_a",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-10T14:30",
        "bitis": "2027-03-10T15:30"
    })
    komutlar.append({
        "komut": "bekleme",
        "kullanici": "w_u90_a",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-10T14:30",
        "bitis": "2027-03-10T15:30"
    })
    komutlar.append({
        "komut": "bekleme",
        "kullanici": "w_u70_b",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-10T14:30",
        "bitis": "2027-03-10T15:30"
    })

    komutlar.append({"komut": "saat", "zaman": "2027-03-08T09:49"})
    komutlar.append({"komut": "giris", "rezervasyon": "r2"})
    komutlar.append({"komut": "saat", "zaman": "2027-03-08T09:50"})
    komutlar.append({"komut": "giris", "rezervasyon": "r2"})

    komutlar.append({"komut": "saat", "zaman": "2027-03-08T10:20"})
    komutlar.append({"komut": "cikis", "rezervasyon": "r2"})

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_tamam_user",
        "kaynak": "YAZ-2",
        "baslangic": "2027-03-08T11:30",
        "bitis": "2027-03-08T12:30"
    })
    komutlar.append({"komut": "saat", "zaman": "2027-03-08T11:25"})
    komutlar.append({"komut": "giris", "rezervasyon": "r4"})

    komutlar.append({
        "komut": "sorgu",
        "tur": "kaynak",
        "id": "YAZ-2",
        "gun": "2027-03-08"
    })

    komutlar.append({"komut": "saat", "zaman": "2027-03-08T12:30"})
    komutlar.append({"komut": "sorgu", "tur": "kullanici", "id": "t_tamam_user"})

    komutlar.append({"komut": "saat", "zaman": "2027-03-10T14:20"})

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_iade_user",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-17T14:00",
        "bitis": "2027-03-17T16:00"
    })

    komutlar.append({"komut": "saat", "zaman": "2027-03-15T08:00"})
    komutlar.append({"komut": "sorgu", "tur": "kullanici", "id": "t_iade_user"})
    komutlar.append({"komut": "iptal", "rezervasyon": "r6"})

    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_iade_user",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-18T14:00",
        "bitis": "2027-03-18T16:00"
    })
    komutlar.append({"komut": "iptal", "rezervasyon": "r7"})
    komutlar.append({"komut": "sorgu", "tur": "kullanici", "id": "t_iade_user"})

    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_sifir",
        "ad": "Test Sifir Bakiye 2",
        "rol": "OGRENCI",
        "sertifikalar": [],
        "bakiye": 0,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_sifir",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-16T10:00",
        "bitis": "2027-03-16T11:00"
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_low",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-17T10:00",
        "bitis": "2027-03-17T11:00"
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_iade_user",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-15T09:00",
        "bitis": "2027-03-15T10:00"
    })
    komutlar.append({
        "komut": "bekleme",
        "kullanici": "t_u1",
        "kaynak": "ODA-1",
        "baslangic": "2027-03-15T09:00",
        "bitis": "2027-03-15T10:00"
    })
    komutlar.append({"komut": "iptal", "rezervasyon": "r8"})

    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_u1",
        "ad": "Coklu Hata ID Oncelik",
        "rol": "UZAYLI",
        "sertifikalar": [],
        "bakiye": -10,
        "guvenilirlik": 80
    })
    komutlar.append({
        "komut": "kullanici_ekle",
        "id": "t_yeni_err",
        "ad": "Coklu Hata Rol Oncelik",
        "rol": "UZAYLI",
        "sertifikalar": [],
        "bakiye": 50,
        "guvenilirlik": 999
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_iade_user",
        "kaynak": "ODA-1",
        "baslangic": "2027-3-16T9:00",
        "bitis": "2027-03-16T10:00"
    })
    komutlar.append({
        "komut": "rezervasyon",
        "kullanici": "t_iade_user",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-15T10:00",
        "bitis": "2027-03-15T12:00"
    })
    komutlar.append({
        "komut": "bekleme",
        "kullanici": "w_u90_a",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-15T10:00",
        "bitis": "2027-03-15T11:00"
    })
    komutlar.append({
        "komut": "bekleme",
        "kullanici": "w_u70_a",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-15T10:30",
        "bitis": "2027-03-15T11:30"
    })
    komutlar.append({
        "komut": "bekleme",
        "kullanici": "w_u70_b",
        "kaynak": "ODA-2",
        "baslangic": "2027-03-15T11:00",
        "bitis": "2027-03-15T12:00"
    })
    komutlar.append({"komut": "iptal", "rezervasyon": "r10"})

    return komutlar


def dogrula_beklenenler(sonuclar: list[dict]) -> None:
    assert len(sonuclar) == 80
    assert sonuclar[6]["kod"] == "ID_MEVCUT"
    assert sonuclar[7]["kod"] == "TANIMSIZ_DEGER"
    assert sonuclar[8]["kod"] == "GECERSIZ_DEGER"
    assert sonuclar[17]["kod"] == "BULUNAMADI"
    assert sonuclar[18]["kod"] == "ZAMAN_ADIMI_HATASI"
    assert sonuclar[19]["kod"] == "GECMIS_ZAMAN"
    assert sonuclar[20]["kod"] == "CALISMA_SAATI_DISI"
    assert sonuclar[21]["kod"] == "SURE_SINIRI"
    assert sonuclar[22]["kod"] == "ILERI_TARIH_SINIRI"
    assert sonuclar[23]["kod"] == "ROL_IZNI_YOK"
    assert sonuclar[25]["kod"] == "SERTIFIKA_YOK"
    assert sonuclar[26]["kod"] == "BAKIM"
    assert sonuclar[27]["kod"] == "KESISME"
    assert sonuclar[28]["kod"] == "HAZIRLIK_IHLALI"
    assert sonuclar[30]["kod"] == "ARDISIK_KULLANIM"
    assert sonuclar[31]["kod"] == "BEKLEME_GEREKSIZ"
    assert sonuclar[32]["kod"] == "SAAT_GERI"
    assert sonuclar[33]["kod"] == "PAKET_BOYUTU" and sonuclar[33]["kalemler"] == []
    assert sonuclar[34]["kod"] == "PAKET_BOYUTU" and sonuclar[34]["kalemler"] == []
    assert sonuclar[35]["kod"] == "GUVENILIRLIK_DUSUK" and sonuclar[35]["kalemler"] == []
    assert sonuclar[36]["kod"] == "PAKET_RED"
    assert sonuclar[37]["kod"] == "PAKET_ICI_KESISME"
    assert sonuclar[38]["kod"] == "BAKIYE_YETERSIZ"
    assert sonuclar[58]["olaylar"][1]["tur"] == "OTOMATIK_ATAMA"
    assert sonuclar[58]["olaylar"][1]["bekleme"] == "b2"
    assert sonuclar[62]["iade"] == 0 and sonuclar[62]["bakiye"] == 120
    assert sonuclar[66]["durum"] == "TAMAM"
    assert sonuclar[67]["durum"] == "RED" and sonuclar[67]["kod"] == "BAKIYE_YETERSIZ"
    assert sonuclar[68]["durum"] == "RED" and sonuclar[68]["kod"] == "ILERI_TARIH_SINIRI"
    assert sonuclar[69]["durum"] == "TAMAM" and sonuclar[69]["rezervasyon_id"] == "r8"
    assert sonuclar[69]["ucret"] == 4 and sonuclar[69]["bakiye"] == 116
    assert sonuclar[70]["durum"] == "TAMAM" and sonuclar[70]["bekleme_id"] == "b4"
    assert sonuclar[70]["sira"] == 1
    assert sonuclar[71]["durum"] == "TAMAM" and sonuclar[71]["iade"] == 0
    assert sonuclar[71]["bakiye"] == 116 and sonuclar[71]["guvenilirlik"] == 95
    assert sonuclar[71]["olaylar"] == [{
        "zaman": "2027-03-15T08:00",
        "tur": "OTOMATIK_ATAMA",
        "bekleme": "b4",
        "rezervasyon": "r9",
        "kullanici": "t_u1",
        "ucret": 4,
        "bakiye": 116,
    }]
    assert sonuclar[72]["durum"] == "RED" and sonuclar[72]["kod"] == "ID_MEVCUT"
    assert sonuclar[73]["durum"] == "RED" and sonuclar[73]["kod"] == "TANIMSIZ_DEGER"
    assert sonuclar[74]["durum"] == "RED" and sonuclar[74]["kod"] == "ZAMAN_ADIMI_HATASI"
    assert sonuclar[75]["durum"] == "TAMAM" and sonuclar[75]["rezervasyon_id"] == "r10"
    assert sonuclar[76]["durum"] == "TAMAM" and sonuclar[76]["bekleme_id"] == "b5" and sonuclar[76]["sira"] == 1
    assert sonuclar[77]["durum"] == "TAMAM" and sonuclar[77]["bekleme_id"] == "b6" and sonuclar[77]["sira"] == 2
    assert sonuclar[78]["durum"] == "TAMAM" and sonuclar[78]["bekleme_id"] == "b7" and sonuclar[78]["sira"] == 3
    assert sonuclar[79]["durum"] == "TAMAM" and sonuclar[79]["iade"] == 4
    assert sonuclar[79]["bakiye"] == 112 and sonuclar[79]["guvenilirlik"] == 95
    assert sonuclar[79]["olaylar"] == [
        {
            "zaman": "2027-03-15T08:00",
            "tur": "OTOMATIK_ATAMA",
            "bekleme": "b5",
            "rezervasyon": "r11",
            "kullanici": "w_u90_a",
            "ucret": 4,
            "bakiye": 116,
        },
        {
            "zaman": "2027-03-15T08:00",
            "tur": "OTOMATIK_ATAMA",
            "bekleme": "b7",
            "rezervasyon": "r12",
            "kullanici": "w_u70_b",
            "ucret": 5,
            "bakiye": 115,
        },
    ]


def main():
    komutlar = uret_testler()

    motor = RezervasyonMotoru()
    motor.yukle(str(KOK_DIZIN / "baslangic.json"))

    sonuclar = []
    for no, cmd in enumerate(komutlar, start=1):
        cmd_copy = json.loads(json.dumps(cmd))
        sonuc = motor.komut_isle(cmd_copy)
        sonuc["no"] = no

        cikti = {"no": no, "komut": sonuc.pop("komut")}
        cikti.update(sonuc)
        sonuclar.append(cikti)

    dogrula_beklenenler(sonuclar)

    senaryo_dizin = KOK_DIZIN / "scenarios"
    senaryo_dizin.mkdir(parents=True, exist_ok=True)

    with open(senaryo_dizin / "test_kapsamli_komutlar.jsonl", "w", encoding="utf-8") as f:
        for cmd in komutlar:
            f.write(json.dumps(cmd, ensure_ascii=False) + "\n")

    with open(senaryo_dizin / "test_kapsamli_beklenen.jsonl", "w", encoding="utf-8") as f:
        for res in sonuclar:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")

    print(
        f"[OK] {len(komutlar)} komutluk scenarios/test_kapsamli_komutlar.jsonl "
        "ve scenarios/test_kapsamli_beklenen.jsonl olusturuldu."
    )


if __name__ == "__main__":
    main()
