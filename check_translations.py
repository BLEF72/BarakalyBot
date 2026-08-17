from texts import TX

missing = []
for key, entry in TX.items():
    if key == "order_status":
        # особый случай - словарь статусов, а не прямая пара ru/uz
        for status, labels in entry.items():
            if "ru" not in labels:
                missing.append(f"order_status.{status}: нет русского перевода")
            if "uz" not in labels:
                missing.append(f"order_status.{status}: нет узбекского перевода")
        continue
    if "ru" not in entry:
        missing.append(f"{key}: нет русского перевода")
    if "uz" not in entry:
        missing.append(f"{key}: нет узбекского перевода")

if missing:
    print(f"❌ Найдено {len(missing)} проблем:")
    for m in missing:
        print(f"  - {m}")
    exit(1)
else:
    print(f"✅ Все {len(TX)} ключей переведены на оба языка")