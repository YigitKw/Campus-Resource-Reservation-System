from __future__ import annotations

import json
import sys

from motor import RezervasyonMotoru


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    if len(sys.argv) < 3:
        print("Kullanim: python main.py <baslangic.json> <komutlar.jsonl>", file=sys.stderr)
        sys.exit(1)

    baslangic_dosyasi = sys.argv[1]
    komut_dosyasi = sys.argv[2]

    motor = RezervasyonMotoru()
    motor.yukle(baslangic_dosyasi)

    with open(komut_dosyasi, "r", encoding="utf-8") as f:
        satirlar = f.readlines()

    for no, satir in enumerate(satirlar, start=1):
        satir = satir.strip()
        if not satir:
            continue

        cmd = json.loads(satir)
        sonuc = motor.komut_isle(cmd)
        sonuc["no"] = no

        cikti: dict = {"no": no, "komut": sonuc.pop("komut")}
        cikti.update(sonuc)

        print(json.dumps(cikti, ensure_ascii=False))


if __name__ == "__main__":
    main()
