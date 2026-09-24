Das Programm ermöglicht mit 2 Tachymetern 


########  Bild  ########

- Der Ursprung der Punktkoordinaten muss im unteren linken Eck liegen
- Die Bildhöhe muss 1 Meter betragen



########  CSV-Datei  ########

- Die csv muss exakt diese Spalten beinhalten: Nr, X, Y, Z
- Eine Linie kann höchstens 1000 Punkte umfassen
- Eine Linie beginnt immer bei einem neuen Tausender 1000, 2000, 3000, etc.
- Nummern unter 1000 werden nicht berücksichtigt



########  Positionierung des Bild im Feld  ########

- Die Reflektoren R1 und R2 bestimmen die Lage und Ausrichtung des Bildes. Die Reflektoren besitzen die lokalen Bildkoordinaten [0,0,0](R1) und [0,1,0](R2)
- Reflektor R3 kann beliebig positioniert werden und dient als Stützpunkt auf der Ebene
- Wird Reflektorlos gemessen, so muss eine Reflektorhöhe von 0 Metern eingetragen werden