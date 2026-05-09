#!/bin/bash

cd /home/sandro/mygest
source venv/bin/activate

python manage.py shell << 'PYTHON_SCRIPT'

from documenti.utils import _format_value

print("=" * 80)
print("TEST: Verifica _format_value con formati Python")
print("=" * 80)

# Test formati Python
test_cases = [
    (2, '02d', '02'),
    (10, '02d', '10'),
    (2026, '04d', '2026'),
    (3.14, '.2f', '3.14'),
    (3.1, '.2f', '3.10'),
]

for value, fmt, expected in test_cases:
    result = _format_value(value, fmt)
    status = "✓" if result == expected else "✗"
    print(f"{status} _format_value({value!r}, {fmt!r}) = {result!r} (expected: {expected!r})")

print()
print("Tutti i test completati!")

PYTHON_SCRIPT
