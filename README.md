# Integracja Home Assistant — smieci_wroclaw

Custom component łączący się z `smieci.example.com` (`/api/ha/v1/*`) i wystawiający harmonogram
wywozu odpadów jako encje Home Assistant, wraz z konfigurowalnymi powiadomieniami.

## Instalacja

### Przez HACS (zalecane)

1. HACS → menu (⋮) w prawym górnym rogu → **Custom repositories**.
2. Dodaj adres `https://github.com/dlvoy/smieci-schedule`, kategoria **Integration**.
3. Znajdź na liście **Harmonogram odpadow (smieci.example.com)** i zainstaluj.
4. Zrestartuj Home Assistant.

### Ręcznie (bez HACS)

Dla instalacji Home Assistant Container / Core bez Supervisora (i tym samym bez HACS) —
skopiuj katalog `custom_components/smieci_wroclaw` do konfiguracji HA. Przez SSH:

```bash
./install.sh user@host /sciezka/do/konfiguracji/ha
```

albo ręcznie: skopiuj `custom_components/smieci_wroclaw/` do `<config>/custom_components/`
i zrestartuj Home Assistant.

### Konfiguracja integracji

Niezależnie od metody instalacji: **Ustawienia → Urządzenia i usługi → Dodaj integrację →
„Harmonogram odpadow”**, podać adres serwisu (domyślnie `https://smieci.example.com`) i token PAT
wygenerowany w `/admin/tokeny` na stronie (zakresy: `schedule:read` + `schedule:refresh`).

## Encje

Jedno urządzenie *Śmieci — <adres>*, na encję/frakcję (5 frakcji: Tworzywa, Zmieszane, BIO,
Papier, Szkło):

- `sensor.smieci_<frakcja>` — najbliższa data (device_class: date), atrybuty: status, dni do
  odbioru, kolor, kolejne terminy.
- `sensor.smieci_<frakcja>_status` — enum: nieznany / zaplanowany / jutro / dzisiaj.
- `binary_sensor.smieci_<frakcja>_wystaw` — włączony gdy jutro lub dzisiaj (do automatyzacji).

Plus: `sensor.smieci_nastepny_odbior`, `sensor.smieci_harmonogram_wazny_do`,
`sensor.smieci_ostatnia_aktualizacja`, `binary_sensor.smieci_polaczenie`,
`button.smieci_odswiez`.

Ikony (`entity_picture`) to kolorowy kosz zgodny z frakcją: pusty kontur gdy zaplanowany,
wypełniony gdy jutro, wypełniony i migający gdy dzisiaj — patrz `custom_components/smieci_wroclaw/icons/README.md`.

## Powiadomienia

W opcjach integracji (**Skonfiguruj**) można dodać dowolną liczbę *celów powiadomień*: encja
`notify.*`, godzina, zdarzenia (jutro/dzisiaj), opcjonalny podzbiór frakcji. Każdy cel rejestruje
własny harmonogram i wysyła komunikat po polsku o pasujących frakcjach.
