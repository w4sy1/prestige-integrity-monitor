# Użycie

`python app.py baseline --root ./dane --baseline baseline.json`
`python app.py check --root ./dane --baseline baseline.json --output reports`
`python app.py update --root ./dane --baseline baseline.json` — podgląd zmian.
`python app.py update --root ./dane --baseline baseline.json --accept-changes`

Baseline zawiera ścieżki względne, rozmiar, mtime i SHA256. Aktualizacja zachowuje poprzedni
plik .bak; można go przywrócić ręcznie po sprawdzeniu. Mtime też wpływa na MODIFIED.
Baseline nie jest podpisany. Przechowuj go poza monitorowanym katalogiem i chroń przed zmianami.
Nie obejmuje dowiązań/junctions, ACL, ADS, strumieni systemowych i VSS.
