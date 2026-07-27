"""Calcolo festività nazionali italiane (fisse + Pasqua/Pasquetta).

Nessuna dipendenza esterna: la Pasqua è calcolata con l'algoritmo di
Gauss/Meeus (calendario gregoriano).
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def easter_sunday(year: int) -> date:
    """Domenica di Pasqua per l'anno dato (algoritmo di Gauss/Meeus)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


@lru_cache(maxsize=64)
def italian_holidays(year: int) -> frozenset[date]:
    """Festività nazionali italiane fisse + Pasqua/Pasquetta per l'anno dato."""
    easter = easter_sunday(year)
    return frozenset(
        {
            date(year, 1, 1),  # Capodanno
            date(year, 1, 6),  # Epifania
            easter,  # Pasqua
            easter + timedelta(days=1),  # Lunedì dell'Angelo (Pasquetta)
            date(year, 4, 25),  # Anniversario della Liberazione
            date(year, 5, 1),  # Festa dei Lavoratori
            date(year, 6, 2),  # Festa della Repubblica
            date(year, 8, 15),  # Ferragosto
            date(year, 11, 1),  # Ognissanti
            date(year, 12, 8),  # Immacolata Concezione
            date(year, 12, 25),  # Natale
            date(year, 12, 26),  # Santo Stefano
        }
    )


def is_italian_holiday(d: date) -> bool:
    """True se la data è una festività nazionale italiana."""
    return d in italian_holidays(d.year)


def is_business_day_it(d: date) -> bool:
    """False se la data cade in weekend o in una festività nazionale italiana."""
    return d.weekday() < 5 and not is_italian_holiday(d)


def next_business_day(d: date) -> date:
    """Ritorna d se è già un giorno feriale, altrimenti il primo giorno feriale successivo."""
    candidate = d
    while not is_business_day_it(candidate):
        candidate += timedelta(days=1)
    return candidate
