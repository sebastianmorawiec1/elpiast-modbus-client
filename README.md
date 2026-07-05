# elpiast-modbus-client

Integracja **Home Assistant** dla sterowników automatyki **EL-PIAST ELP11R32L (MAX L+)**
central wentylacyjnych, po protokole **Modbus TCP/IP** (moduł ELP11R32L-MOD-IP+ z kartą Ethernet).

Mapa **ponad 160 kluczowych zmiennych** opracowana na podstawie oficjalnej DTR 183-03-2021
MAX L+ v6.4 (rozdz. 8 „Zmienne Modbus RTU"): temperatury (B1–B8, PT1–5), tryb pracy (WorkMode),
nastawa temperatury (Tset), wilgotność, CO2, falowniki nawiew/wywiew (prąd, Hz, RPM), pompy,
nagrzewnice (wodna/elektryczna/gazowa), chłodnice, odzysk, komora mieszania oraz ~35 alarmów.
Pełna lista zmiennych DTR obejmuje 403 pozycje — pozostałe (serwisowe, emulacje we/wy) można
dodać własnym plikiem `registers.yaml` w tym samym formacie.

## Adresowanie (ważne!)

Zmienne sterownika są 32-bitowe w formacie **Fixed** (wartość × 256). Integracja używa
16-bitowych przestrzeni adresowych sterownika:
- **Fixed** → adres `0x7000 + (adres_tabeli / 2)`, wartość ×100 → `scale: 0.01`
- **Multistate** → adres `0x4000 + (adres_tabeli / 2)`, `scale: 1`

## Instalacja (HACS)

1. HACS → Custom repositories → `https://github.com/sebastianmorawiec1/elpiast-modbus-client`, typ *Integration*.
2. Zainstaluj **EL-Piast Modbus** → restart HA.
3. Ustawienia → Urządzenia i usługi → Dodaj integrację → **EL-Piast Modbus** → IP sterownika, port 502.

Encje dostają stabilne ID z prefiksem hosta, np. `sensor.elp_192_168_1_70_b1`.

## Licencja

MIT
