import json
from pathlib import Path
import sys

KOK_DIZIN = Path(__file__).resolve().parent.parent


def derin_karsilastir(yol: str, beklenen, uretilen) -> list[str]:
    hatalar = []
    if type(beklenen) is not type(uretilen):
        if isinstance(beklenen, (int, float)) and isinstance(uretilen, (int, float)):
            if beklenen != uretilen:
                hatalar.append(f"{yol}: sayisal deger farkli (beklenen={beklenen}, uretilen={uretilen})")
            elif type(beklenen) is not type(uretilen):
                hatalar.append(f"{yol}: tip farkli (beklenen={type(beklenen).__name__}, uretilen={type(uretilen).__name__})")
        else:
            hatalar.append(f"{yol}: tip uyusmazligi (beklenen={type(beklenen).__name__}, uretilen={type(uretilen).__name__})")
        return hatalar

    if isinstance(beklenen, dict):
        bek_anahtarlar = set(beklenen.keys())
        ure_anahtarlar = set(uretilen.keys())

        eksik = bek_anahtarlar - ure_anahtarlar
        if eksik:
            hatalar.append(f"{yol}: eksik anahtarlar: {eksik}")

        for k in bek_anahtarlar & ure_anahtarlar:
            alt_yol = f"{yol}.{k}" if yol else k
            hatalar.extend(derin_karsilastir(alt_yol, beklenen[k], uretilen[k]))

    elif isinstance(beklenen, list):
        if len(beklenen) != len(uretilen):
            hatalar.append(f"{yol}: liste uzunlugu farkli (beklenen={len(beklenen)}, uretilen={len(uretilen)})")
        for i, (b_eleman, u_eleman) in enumerate(zip(beklenen, uretilen)):
            alt_yol = f"{yol}[{i}]"
            hatalar.extend(derin_karsilastir(alt_yol, b_eleman, u_eleman))

    else:
        if beklenen != uretilen:
            hatalar.append(f"{yol}: deger farkli (beklenen={repr(beklenen)}, uretilen={repr(uretilen)})")

    return hatalar


def jsonl_oku(dosya_adi: str) -> list[str]:
    for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le"):
        try:
            with open(dosya_adi, "r", encoding=enc) as f:
                satirlar = [line.strip() for line in f if line.strip()]
                if satirlar:
                    json.loads(satirlar[0])
                return satirlar
        except (UnicodeError, json.JSONDecodeError):
            continue
    with open(dosya_adi, "r", encoding="utf-8", errors="replace") as f:
        return [line.strip() for line in f if line.strip()]


def main() -> int:
    beklenen_yol = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(KOK_DIZIN / "scenarios" / "beklenen_sonuclar.jsonl")
    )
    uretilen_yol = sys.argv[2] if len(sys.argv) > 2 else str(KOK_DIZIN / "sonuclar.jsonl")

    try:
        beklenen_satirlar = jsonl_oku(beklenen_yol)
    except FileNotFoundError:
        print(f"[HATA] {beklenen_yol} dosyasi bulunamadi!")
        return 1

    try:
        uretilen_satirlar = jsonl_oku(uretilen_yol)
    except FileNotFoundError:
        print(f"[HATA] {uretilen_yol} dosyasi bulunamadi!")
        return 1

    print(f"Toplam beklenen satir sayisi : {len(beklenen_satirlar)}")
    print(f"Toplam uretilen satir sayisi : {len(uretilen_satirlar)}")

    if len(beklenen_satirlar) != len(uretilen_satirlar):
        print("[HATA] Satir sayilari esit degil!")
        return 1

    toplam_hata = 0

    for no, (b_satir, u_satir) in enumerate(zip(beklenen_satirlar, uretilen_satirlar), start=1):
        try:
            b_json = json.loads(b_satir)
        except Exception as e:
            print(f"[HATA] Satir {no} beklenen JSON parse hatasi: {e}")
            toplam_hata += 1
            continue

        try:
            u_json = json.loads(u_satir)
        except Exception as e:
            print(f"[HATA] Satir {no} uretilen JSON parse hatasi: {e}")
            toplam_hata += 1
            continue

        farklar = derin_karsilastir(f"Satir {no}", b_json, u_json)
        if farklar:
            toplam_hata += len(farklar)
            print(f"\n[UYUMSUZLUK] Satir {no}:")
            for fark in farklar:
                print(f"  - {fark}")
            print(f"  Beklenen: {b_satir}")
            print(f"  Uretilen: {u_satir}")
        else:
            komut = b_json.get("komut")
            durum = b_json.get("durum")
            print(f"Satir {no:2d} [{durum:5s}] komut='{komut}': ESLESME OK")

    if toplam_hata == 0:
        print("\n=======================================================")
        print(f"[BASARILI] 1'den {len(beklenen_satirlar)}'e kadar TUM satirlar")
        print("beklenen_sonuclar.jsonl ile %100 ALAN ALAN ESLESIYOR!")
        print("=======================================================")
        return 0
    else:
        print(f"\n[BASARISIZ] Toplam {toplam_hata} uyumsuzluk tespit edildi.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
