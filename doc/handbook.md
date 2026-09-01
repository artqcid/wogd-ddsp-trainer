# WOGD DDSP-Trainer – Bedienungsanleitung

_Diese Anleitung beschreibt die Bedienung des Trainings in der WOGD
DDSP-Trainer-Web-App. Sie behandelt ausschließlich das Arbeiten mit der
Anwendung (Datensätze anlegen, Modelle trainieren, überwachen und
konfigurieren) – keine Installation und keine Entwicklungsdetails._

---

## Inhalt

1. [Überblick und Navigation](#1-überblick-und-navigation)
2. [Kurzanleitung – Standardmodell in wenigen Schritten](#2-kurzanleitung--standardmodell-in-wenigen-schritten)
3. [Komplexere Modelle](#3-komplexere-modelle)
   - 3.1 [Component-Modelle](#31-component--harmonische-obertöne-und-rauschfilter-balancieren)
   - 3.2 [Hacks-Modelle](#32-hacks--synthese-experimente)
   - 3.3 [Engine-Modelle](#33-engine--alternative-synthese-engines)
   - 3.4 [Advanced-Modelle](#34-advanced--latenter-raum-polyfonie-und-voice-conversion)
4. [Parameter-Referenz](#4-parameter-referenz)
   - 4.1 [Presets (FAST / NORMAL / QUALITY)](#41-presets-fast--normal--quality)
   - 4.2 [Trainings-Konfiguration (Core)](#42-trainings-konfiguration-core)
   - 4.3 [Component-Parameter](#43-component-parameter)
   - 4.4 [Hacks-Parameter](#44-hacks-parameter)
   - 4.5 [Engine-Parameter](#45-engine-parameter)
   - 4.6 [Advanced-Parameter](#46-advanced-parameter)
   - 4.7 [Inferenz-Parameter (VST-Knöpfe & Playground)](#47-inferenz-parameter-vst-knöpfe--playground)

---

## 1. Überblick und Navigation

Die Anwendung ist eine Web-App mit dunkler Oberfläche und einer Seitenleiste
(Sidebar) links. Die Sidebar organisiert den kompletten Arbeitsablauf in vier
Gruppen:

| Gruppe | Aufgabengebiet |
|---|---|
| **Dataset & Preprocessing** | Audio hochladen, Datensätze verwalten, Merkmale (Features) extrahieren |
| **Model Architecture** | Modelltyp festlegen, Training konfigurieren, Presets verwalten |
| **Training & Monitor** | Training starten/überwachen, TensorBoard, Run-Verwaltung |
| **Inference & Export** | Synthese im Playground, Modell-Export (Neutone / Custom VST) |

Oben rechts zeigt die **Statusleiste** jederzeit den Zustand des Backends, der
GPU (Name + VRAM) und von TensorBoard an.

> **Wichtig:** Die App arbeitet **lokal**. Die verfügbare GPU wird automatisch
> analysiert, und sinnvolle Trainingsparameter werden an die vorhandene
> VRAM-Größe angepasst vorgeschlagen. Alle Werte werden automatisch auf die
> Grenzen der GPU begrenzt („geclampt"), wenn sie außerhalb liegen.

### Die fünf Modelltypen (Tiers)

Die App unterscheidet fünf Komplexitätsstufen. Jede Stufe baut auf der
vorherigen auf und aktiviert weitere Funktionen:

| Stufe | Name | Was es kann | Empfohlene GPU |
|---|---|---|---|
| 🟢 `standard` | Standard | Saubere Sprach-/Gesangssynthese; harmonischer Oszillator + gefiltertes Rauschen + Hall | ab 4 GB |
| 🔵 `component` | Component | Standard + explizite Balance zwischen Obertönen und Rauschanteil | ab 4 GB |
| 🟡 `hacks` | Hacks | Component + Synthese-Experimente (FM, Phasenverzerrung, LFO, Wavetable) | ab 4 GB |
| 🟣 `engine` | Engine | Hacks + alternative Synthese-Engines (Sinusoidal, Comb-Subtractive, NEWT) | ab 4 GB |
| 🔴 `advanced` | Advanced | Engine + VAE-Latentraum, polyfone Modelle (bis 4 Stimmen), Voice Conversion | 6–12 GB |

Der gewählte Modelltyp wird als farbiges Badge in der Statusleiste angezeigt
und gilt für den gesamten Trainingslauf.

---

## 2. Kurzanleitung – Standardmodell in wenigen Schritten

Dieser Abschnitt führt durch das **einfachste** Szenario: ein sauberes
Standardmodell für Sing-/Sprachsynthese.

### Schritt 1: Audiodaten hochladen

1. Öffne in der Sidebar **Dataset & Preprocessing** → **Upload & Ingestion**.
2. Ziehe deine Audiodateien per Drag & Drop in das Upload-Feld oder klicke
   darauf, um Dateien auszuwählen.
   - Unterstützte Formate: **WAV, FLAC, OGG, MP3, M4A, MP4, AIFF, AIF**.
   - Zu jeder Datei wird eine Wellenform-Vorschau angezeigt.
3. Klicke **Upload**.

> **DDSP-Datenanforderungen:** Für ein gutes Timbre-Modell werden typischerweise
> **10–15 Minuten** sauberes, durchgängiges Audiomaterial empfohlen (mindestens
> aber 2–5 Minuten). Das Audio sollte **monophon** und „trocken" sein – also
> ohne Hall, Delay oder andere starke Effekte. **Polyphones** Audio führt zu
> falscher Tonhöhen-Erkennung (Pitch-Tracking).

### Schritt 2: Merkmale extrahieren (Preprocessing)

1. Öffne **Dataset & Preprocessing** → **Preprocessing**.
2. Wähle oben deinen Datensatz aus.
3. Starte die Merkmalsextraktion. Dabei werden zwei Merkmale berechnet:
   - **F0 (Tonhöhe / Grundfrequenz)** – mit Pitch-Tracking; eine Warnung
     erscheint, wenn die Tracking-Zuverlässigkeit zu niedrig ist.
   - **Lautstärke (Loudness)** – A-bewertete Leistung.
4. Warte bis die Extraktion abgeschlossen ist (Fortschrittsanzeigen).

Der Datensatz ist danach trainierfähig.

### Schritt 3: Modell konfigurieren (Wizard)

1. Öffne **Model Architecture** → **Training Config**.
   - Beim ersten Besuch öffnet sich automatisch der **Model Setup Wizard**.
   - Fortgeschrittene können den Wizard mit **Skip** überspringen
     (Standard-Stufe wird dann angenommen) oder jederzeit über
     **⚙ Reconfigure Model** erneut öffnen.
2. **Schritt 1 – Modelltyp (Model Tier):** Wähle die Karte **Standard**.
   Nicht passende Stufen sind ausgegraut, wenn sie nicht in die GPU passen
   (erkennbar am ✓- bzw. ⚠-Badge).
3. **Schritt 2 – Qualität / Preset:** Wähle eine der drei Geschwindigkeitsstufen
   (Details siehe [Kap. 4.1](#41-presets-fast--normal--quality)):
   - **FAST** – klein, sehr schnelles Training, dafür geringere Qualität
     (~25 % der GPU-Auslastung).
   - **NORMAL** – ausgewogen (~50 % GPU-Auslastung).
   - **QUALITY** – beste Qualität, langes Training (~90–100 % GPU-Auslastung).
   - Die geschätzte VRAM-Auslastung wird für jede Stufe angezeigt.
4. **Schritt 3 – Zielmodus:**
   - **Offline / Studio** – beste Qualität, höhere Latenz.
   - **Realtime / Low-Latency** – für Echtzeit-Einsatz optimiert.
5. Klicke **Start Training Setup ✓**.

### Schritt 4: Training starten

Nach dem Wizard findest du dich im Tab **Core** wieder:

1. Prüfe die Werte im Tab **Core**:
   - **Preset:** Das gewählte Preset ist voreingestellt.
   - **Learning Rate, Batch Size, Epochs** (Anzahl Trainingsepochen),
     **Decoder Type** (GRU oder RNN) und **Enable Reverb** (Hall ein/aus).
2. Klicke den Button **▶ Start Training**.

Der Trainingslauf („Run") wird angelegt und beginnt. Seine ID und sein Status
werden angezeigt.

### Schritt 5: Training überwachen

1. Öffne **Training & Monitor** → **Training Dashboard**.
2. Der TensorBoard-Bereich zeigt **Loss-Kurven, Spektrogramme und
   Checkpoint-Audio** – eingebettet direkt in der Ansicht. Sollte die
   Einbettung blockiert sein, öffne TensorBoard über den Link in einem neuen
   Tab.
3. In der Run-Liste kannst du jeden Lauf:
   - **Stoppen** (kooperativer Stopp am Ende des nächsten Schritts),
   - **Fortsetzen (Resume)** – Training wird ab dem neuesten Checkpoint 
     fortgesetzt,
   - **Löschen**,
   - als **Preset speichern** („Save as Preset" übernimmt die effektiven
     Parameter als eigenes Preset).

Das fertige Modell kannst du anschließend im **Inference & Export**-Bereich
testen und exportieren (Neutone-Plug-in oder Custom VST, siehe Kap. 4.7).

---

## 3. Komplexere Modelle

Alle fünf Stufen folgen demselben Grundablauf wie in der Kurzanleitung –
der Unterschied liegt im **Wizard-Schritt 1 (Modelltyp)** und in den
anschließend verfügbaren **Tabs** im Training Config-Bereich.

Wichtig: Nach dem Abschluss des Wizards erscheint eine **Tab-Leiste** mit den
Registern `Core | Component | Hacks | Engine | Advanced`. Register, deren
Stufe höher liegt als die gewählte, sind ausgegraut und nur über einen
„Upgrade"-Link freischaltbar.

---

### 3.1 Component – harmonische Obertöne und Rauschfilter balancieren

**Zweck:** Beim Standardmodell mischt das Modell Obertöne (harmonischer
Oszillator) und Rauschen (gefiltertes Rauschsignal) automatisch. Im
`component`-Modell steuerst du diese Balance **explizit** über die Anzahl der
Obertöne und Rauschfilterbänke – Grundlage für feinere Klang- und Textur-Einstellungen.

**So erstellt man es:**

1. Wizard-Schritt 1: Karte **Component** wählen.
2. Wizard-Schritt 2: Qualität wählen (FAST / NORMAL / QUALITY).
3. Wizard-Schritt 3: Zielmodus wählen.
4. Im Tab **Component**:
   - **Number of Harmonics:** Anzahl der sinusförmigen Obertöne (Schieberegler;
     je nach GPU 20–120).
   - **Number of Filter Banks:** Anzahl der Rauschfilterbänke (Schieberegler;
     je nach GPU 16–64).
5. Optional: **Open Component Mixer →** öffnet eine Detail-Ansicht, in der die
   Gewichtungen von harmonischem und Rauschanteil feinjustiert werden können.
6. Training starten wie gehabt mit **▶ Start Training**.

> **Hinweis:** Als `component`-Modell exportierte Dateien erlauben im Custom VST
> bis zu **8 Inferenz-Parameter** (empfohlen 4–6), z. B. `Harmonic Blend` und
> `Noise Blend` als Knöpfe.

---

### 3.2 Hacks – Synthese-Experimente

**Zweck:** Die Stufe `hacks` aktiviert experimentelle Synthese-Modifikationen
am Modellkern. So entstehen Klangfarben jenseits der sauberen
Sprachsynthese – von FM-Klängen über Phasenverzerrung bis zu LFO-Modulation
und lernbaren Wavetables. **Experimentell:** Ergebnisse sind weniger
vorhersehbar.

**So erstellt man es:**

1. Wizard-Schritt 1: Karte **Hacks** wählen.
2. Wizard-Schritte 2 und 3: Qualität und Zielmodus wählen.
3. Im Tab **Hacks** die gewünschten Synthese-Hacks aktivieren:
   - **Waveform:** Grundwellenform der Oszillation – `Sine`, `Square` oder
     `Saw` (Sinus, Rechteck, Sägezahn).
   - **FM Depth:** Frequenzmodulation – Modulationstiefe (0 = aus).
   - **FM Ratio:** Verhältnis Modulator-/Trägerfrequenz.
   - **Phase Distortion (pd_k):** Phasenverzerrung im Stil des Casio-CZ-
     Synthesizers (Werte 0–1).
   - **LFO:** Aktivieren; mit **LFO Frequency** (Frequenz) und LFO-Tiefe.
   - **Trainable Wavetable:** lernbare Wavetable als Oszillatorquelle.
   - **Angular Cumsum:** Phasendreh-Korrektur (behebt Klangartefakte bei
     bestimmten Wellenformen).
4. Optional: **Open Synth Hacks →** öffnet die ausführliche
   Experimentier-Ansicht mit weiteren Parametern (z. B. harmonische
   Verhältnisse `harmonic_ratios`, Rauschfarbe).
5. Training starten mit **▶ Start Training**.

> **Hinweis für den Export:** Der Satz der vorgeschlagenen Inferenz-Parameter
> hängt davon ab, **welche Hacks** aktiv waren – z. B. erscheinen bei aktivem
> FM-Hack `FM Depth` und `FM Ratio` als Knöpfe, bei aktivem Phasenverzerrungs-
> Hack `PD Amount` und `Waveshape`.

---

### 3.3 Engine – alternative Synthese-Engines

**Zweck:** Statt der Standard-Engine (harmonischer Oszillator + Rauschen) kann
das Modell eine von **vier Synthese-Engines** verwenden. Jede erzeugt einen
anderen klanglichen Grundcharakter:

| Engine | Klangcharakter | Typische Parameter |
|---|---|---|
| **Harmonic** | Klassische DDSP-Synthese (Standard) | – |
| **Sinusoidal** | Reine Sinus-Partials, glasiger Klang | `Inharmonicity`, `Partial Density`, `Brightness` |
| **Comb-Subtractive** | Kammsfilter-Charakter (Körper-/Resonanzton) | `Formant Shift`, `Vowel`, `Roughness` |
| **NEWT** | Neural Waveshaping Unit – neural verformte Wellenform | `Tone Character`, `Saturation`, `Odd Harmonics` |

**So erstellt man es:**

1. Wizard-Schritt 1: Karte **Engine** wählen.
2. Wizard-Schritte 2 und 3: Qualität und Zielmodus wählen.
3. Im Tab **Engine**:
   - **Engine:** wähle `Harmonic`, `Sinusoidal`, `Comb-Subtractive` oder `NEWT`.
   - **Noise Color** (nur bei Sinusoidal / Comb-Subtractive): Rauschfarbe
     `White` (weiß), `Pink` (rosa) oder `Brown` (braun).
   - **NEWT Hidden Size / Layers** (nur bei NEWT): Größe und Tiefe der
     neuralen Waveshaping-Filter.
4. Training starten mit **▶ Start Training**.

> **Hinweis:** Der Engine-Typ bestimmt auch die vorgeschlagenen
> Inferenz-Knöpfe beim Export – z. B. `Tone Character` und `Saturation` bei
> NEWT, `Formant Shift` bei Comb-Subtractive.

---

### 3.4 Advanced – latenter Raum, Polyfonie und Voice Conversion

**Zweck:** Die höchste Stufe kombiniert drei Expertinnen-Features. Sie benötigt
die meiste GPU-Leistung (empfohlen **6–12 GB VRAM**). In der Stufe `advanced`
stehen drei Bereiche im Tab **Advanced** zur Verfügung:

- **VAE / Latent Space:** ein latenter (komprimierter) Raum zur
  Timbre-Steuerung – ideal zum Mischen und Morphing von Klängen.
- **Polyphony:** ein Modell mit mehreren Stimmen (`n_voices`) für polyfone
  Synthese (bis zu 4 Stimmen).
- **Voice Conversion:** Voice-Conversion – aus einer Quell-Stimme wird mit
  Hilfe eines Inhalts-Encoders eine Ziel-Timbre erzeugt.

**Warnung im Tab:** Bei mehr als 2 Stimmen erscheint der Hinweis
*„N voices × ~2,2 GB. Ensure sufficient VRAM."* – jede Stimme kostet etwa das
VRAM eines Basismodells.

---

#### Variante A: VAE / Latent Space (Timbre-Steuerung & Morphing)

1. Wizard-Schritt 1: Karte **Advanced** wählen (⚠ bei zu wenig VRAM).
2. Tab **Advanced** → Abschnitt **VAE / Latent Space**:
   - **Use Latent (VAE)** aktivieren.
   - **Latent Dim:** Dimension des latenten Raums (Standard **32**; Bereich 8–128).
   - **KL Beta:** Gewichtung des KL-Verlusts (Regularisierung). Höhere Werte
     erzwingen eine „glattere", geordnetere – aber weniger detailreiche –
     Verteilung.
3. Training starten.
4. Nach dem Training (im **Inference & Export**-Bereich):
   - **Latent Explore:** erkundet, wie jede latente Dimension (Z1…ZN) den
     Klang verändert; Du kannst Dimensionen beschriften (z. B. „Rauigkeit",
     „Helligkeit").
   - **Morphing:** webt einen Übergang zwischen zwei Checkpoints A und B.
   - Beim **Export** erscheinen die latenten Dimensionen als Knöpfe (Timbre Z1…ZN);
     am besten nutzt Du das Custom-VST-Ziel mit bis zu **16 Parametern**.

#### Variante B: Polyfonie (mehrere Stimmen)

1. Wizard-Schritt 1: Karte **Advanced** wählen.
2. Tab **Advanced** → Abschnitt **Polyphony**:
   - **Number of Voices:** 1–4 Stimmen. Jede zusätzliche Stimme vervielfacht den
     VRAM-Bedarf des Basismodells (~2,2 GB pro Stimme).
3. Training starten.
4. Typische Inferenz-Knöpfe nach dem Export: `Voice Balance`, `Detune`,
   `Voice Spread`, `Unison Width`.

#### Variante C: Voice Conversion

1. Wizard-Schritt 1: Karte **Advanced** wählen.
2. Tab **Advanced** → Abschnitt **Voice Conversion**:
   - **Use Content Encoder** aktivieren.
   - **Encoder:** `HuBERT-Soft` oder `ContentVec`.
3. Training starten.
4. Im **Voice Conversion**-Bereich (eigene Ansicht) Quell- und Zielmodell
   wählen und konvertieren. Typische Inferenz-Knöpfe: `Style Transfer`,
   `Formant Scale`, `Breathiness`, `Speaker Blend`.

---

## 4. Parameter-Referenz

In der App gibt es **zwei komplett getrennte** Parameter-Ebenen:

- **Schicht 1 – Trainings-Konfiguration (Architektur-Parameter):** legt die
  Modellarchitektur fest, wird beim Training eingebettet und ist danach
  unveränderlich. Diese Parameter erscheinen **niemals** als VST-Knöpfe.
- **Schicht 2 – Inferenz-Parameter (Laufzeit-Parameter):** steuern das Modell
  zur Laufzeit (die VST-Knöpfe bzw. Playground-Schieberegler) und werden vor
  dem Export im Parameter-Builder konfiguriert.

---

### 4.1 Presets (FAST / NORMAL / QUALITY)

Die drei eingebauten Presets sind **relativ zur GPU-Größe** skaliert. Jede
Stufe drückt ein Ziel für die VRAM-Auslastung aus; auf einer 6-GB-GPU sind die
absoluten Werte kleiner als auf einer 12-GB-GPU, das Verhältnis ist gleich.

| Preset | VRAM-Ziel | Effekt |
|---|---|---|
| **FAST** | ~25 % | Kleine `hidden_size`, minimale STFT-Skalen, gemischte Präzision erzwungen, Gradient-Checkpointing aktiv → schnellstes Training |
| **NORMAL** | ~50 % | Mittlere `hidden_size`, moderate Werte → ausgewogen |
| **QUALITY** | ~90–100 % | Maximale `hidden_size`, maximale STFT-Skalen, kein Checkpointing → beste Qualität, längstes Training |

Außerdem kannst Du **eigene Presets** anlegen (Preset Manager) oder die
Parameter eines abgeschlossenen Laufs als Preset sichern („Save as Preset" im
Training Dashboard). Werte außerhalb der GPU-Grenzen werden beim Speichern
automatisch begrenzt und als „geclampt" gekennzeichnet. Ein **Rebase-Hinweis**
erscheint, wenn ein Preset für eine andere Modellstufe erstellt wurde.

---

### 4.2 Trainings-Konfiguration (Core)

Tab **Core** (alle Stufen):

| Parameter | Bedeutung | Typische Werte |
|---|---|---|
| **Learning Rate** | Lernrate des Optimierers (Adam/AdamW). Zu hoch → instabiles Training, zu niedrig → sehr langsames Ausbilden. | 1e-6 … 1e-1; **Default 1e-3** |
| **Batch Size** | Anzahl der Sequenzen pro Optimierungsschritt. DDSP hat keine batch-abhängigen Schichten – **1** ist der empfohlene und voreingestellte Wert. | Default **1** |
| **Epochs** | Anzahl der Durchläufe über den kompletten Datensatz. Mehr Epochen = mehr Feinschliff, aber auch mehr Zeit und Overfit-Risiko. | z. B. **100** |
| **Decoder Type** | Architektur des Decoders. **GRU** (gated recurrent unit) ist die Standardwahl; **RNN** ist leichter, aber etwas leistungsschwächer. | `GRU`, `RNN` |
| **Enable Reverb** | Aktiviert einen trainierbaren Hall in der Modellpipeline. Während des Trainings oft optional; für „trockene" Klänge deaktivierbar. | ein/aus |

Grundparameter, die die GPU-Detektion vorschlägt und automatisch begrenzt
(je nach vorhandenem VRAM):

| Parameter | Bedeutung |
|---|---|
| **Hidden Size** | Größe der verborgenen Schicht des Encoders/Decoders. Größter VRAM-Faktor. Kleinere Werte (z. B. 128/256) sparen ~40 % Aktivierungsspeicher bei minimalem Qualitätsverlust. |
| **STFT Scales** | Anzahl der Auflösungen in der Mehr-Skalen-Spektral-Loss-Berechnung (3, 5 oder 8). Mehr Skalen = feinere Verlustberechnung, teurer. |

**VRAM-Faustregeln der App:**

| Verfügbares VRAM | Hidden Size | STFT-Skalen | Mixed Precision | Checkpointing |
|---|---|---|---|---|
| < 4 GB | 128–256 | 3 | erzwungen | aktiviert |
| 4–8 GB | 256–512 | 3 | erzwungen | optional |
| 8–12 GB | 512 | 5 | empfohlen | deaktiviert |
| ≥ 12 GB | 512–1024 | 5–8 | optional | deaktiviert |

**Weitere Core-bezogene Parameter:**

| Parameter | Bedeutung |
|---|---|
| **Mixed Precision** | Trainingsmodus: `required` (fp16 erzwungen, halbiert Aktivierungsspeicher), `recommended`, `optional`. |
| **Gradient Checkpointing** | Tauscht ~20 % Rechenzeit gegen ~3× weniger Aktivierungs-VRAM (`enabled` / `optional` / `disabled`). |

---

### 4.3 Component-Parameter

Tab **Component** (Stufe `component` und höher):

| Parameter | Bedeutung |
|---|---|
| **Number of Harmonics** | Anzahl der sinusförmigen Obertöne des harmonischen Oszillators (GPU-grenzabhängig 20–120). Mehr Obertöne = metallischer/brillanter, aber teurer. |
| **Number of Filter Banks** | Anzahl der Filter in der gefilterten-Rausch-Pipeline (GPU-grenzabhängig 16–64). Mehr Bänke = feiner aufgelöste Rausch-/Textur-Komponente. |

---

### 4.4 Hacks-Parameter

Tab **Hacks** (Stufe `hacks` und höher). Alle Felder defaulten auf das
Standard-Verhalten (deaktiviert) – nichts davon beeinflusst bestehende
Standardmodelle.

| Parameter | Bedeutung |
|---|---|
| **Waveform** | Oszillator-Grundwellenform (nur für nicht-sinusförmige Synthese): `Sine`, `Square`, `Saw`. |
| **FM Depth** | Tiefe der Frequenzmodulation. 0 = FM aus. >0 erzeugt inharmonische/metallische Spektren. |
| **FM Ratio** | Frequenzverhältnis Modulator : Träger (z. B. 2 = eine Oktave über dem Träger). |
| **Phase Distortion (pd_k)** | Phasenverzerrung im Stil des Casio-CZ-Synthesizers (0 = unverzerrt, 1 = stark). |
| **LFO (Use LFO)** | Aktiviert einen Low-Frequency-Oszillator zur Modulation der Synthese. |
| **LFO Frequency** | Frequenz des LFO (nur bei aktivem LFO sichtbar). |
| **LFO Depth** | Modulationstiefe des LFO. |
| **Trainable Wavetable** | Verwendet eine **lernbare** Wavetable als Oszillatorquelle statt der festen Wellenform. |
| **Angular Cumsum** | Phasenintegration per kumulativer Summe statt kumulativem Phasenspeicher – behebt Drift-Artefakte bei Rechteck-/Sägezahn-Wellenformen. |

In der erweiterten **Synth Hacks**-Ansicht zusätzlich:

| Parameter | Bedeutung |
|---|---|
| **Harmonic Ratios** | Individuelle Frequenz-Verhältnisse der Obertöne (inharmonisches „Rauigkeit"-Design). |
| **Band Mask (low/high)** | Maske für den Spektral-Loss auf einen Frequenzbereich – lenkt den Loss gezielt (z. B. nur auf tiefe Bänder). |

---

### 4.5 Engine-Parameter

Tab **Engine** (Stufe `engine` und höher):

| Parameter | Bedeutung |
|---|---|
| **Engine** | Auswahl der Synthese-Engine: `harmonic`, `sinusoidal`, `combsub`, `newt`. |
| **Noise Color** | Rauschfarbe des Rauschgenerators (`white` / `pink` / `brown`) – nur bei Sinusoidal/Comb-Subtractive. Weiß = alle Frequenzen gleich, Rosa = −3 dB/Oktave, Braun = −6 dB/Oktave (dumpfer). |
| **NEWT Hidden Size** | Größe der verborgenen Schicht des NEural Waveshaping Transformers (min 16, max 256). |
| **NEWT Layers** | Anzahl der Lagen des neuronalen Waveshaping-Transformers (1–8). Mehr Lagen = mehr nichtlineare Verformung möglich, teurer. |
| **Noise Grain Jitter** | (Synth-Hacks-Ansicht) Zufälligkeit/Variation des Kornzeitpunkts beim granularen Rauschanteil. |

---

### 4.6 Advanced-Parameter

Tab **Advanced** (Stufe `advanced`):

**VAE / Latent Space:**

| Parameter | Bedeutung |
|---|---|
| **Use Latent (VAE)** | Aktiviert den VAE-Encoder und einen latenten Raum. Grundlage für Timbre-Morphing und gezielte Klangsteuerung. |
| **Latent Dim** | Anzahl der latenten Dimensionen (Default **32**, Bereich 8–128). Die relevantesten Dimensionen werden per PCA-Analyse des Datensatzes identifiziert. |
| **KL Beta** | Gewichtung des KL-Divergenz-Verlusts (0–10). Regelt einerseits Regularisierung (glattere, geordnetere Verteilung), andererseits Detailtreue. |
| **KL Warmup Steps** | Anzahl der Anfangsschritte, in denen der KL-Anteil allmählich hochgedreht wird (stabilisiert frühes Training – hinter den Kulissen vorbelegt). |

**Polyphony:**

| Parameter | Bedeutung |
|---|---|
| **Number of Voices** | Anzahl der gleichzeitig trainierten Stimmen (1–4). **VRAM × n** – bei >2 Stimmen erscheint eine Warnung. Mehr Stimmen erlauben Akkorde/polyfone Synthese. |

**Voice Conversion:**

| Parameter | Bedeutung |
|---|---|
| **Use Content Encoder** | Aktiviert einen festen Inhalts-Encoder für Voice Conversion (der Encoder ist eingefroren, also nicht mittrainierbar). |
| **Content Encoder Name** | `HuBERT-Soft` oder `ContentVec` (unterschiedliche Sprachrepräsentationen/Qualität). |

---

### 4.7 Inferenz-Parameter (VST-Knöpfe & Playground)

Diese Parameter werden **für den Export** im Parameter-Builder konfiguriert
(Model Export, Komponente `ModelParameterBuilder`) und steuern das Modell zur
Laufzeit. Sie ändern **nicht** die Modellgewichte. Einschränkungen:

- **Neutone FX:** höchstens **4** Knöpfe (fest vorgegeben durch das Plug-in).
  Pro Parameter einstellbar: Name (≤ 30 Zeichen), Beschreibung, Typ,
  Min/Max/Default, Mapping, Einheit, Gruppe.
- **Custom VST:** bis zu **16** Parameter (eigenes VST-Format, TorchScript),
  nur für Stufen ≥ `component` sichtbar.
- **API / Offline:** unbegrenzt über JSON.

Für jede Stufe werden beim ersten Öffnen sinnvolle **Standard-Knöpfe**
vorgeschlagen (überschreibbar). Pro Karte einstellbar:

| Feld | Bedeutung |
|---|---|
| **Name** | Anzeigename des Knopfs (max. 30 Zeichen). |
| **Beschreibung** | Tooltip-Text (max. 150 Zeichen). |
| **Typ** | `continuous` (stufenlos) oder `categorical` (Auswahl mit Labels). |
| **Min / Max / Default** | Wertebereich und Startwert des Knopfs. |
| **Mapping** | Regler-Kennlinie: `linear`, `log` (logarithmisch, für Frequenzartige Größen) oder `exp` (exponentiell, für Verstärkungsartige). |
| **Einheit (Unit Hint)** | Suffix im VST-UI, z. B. `st` (Halbtöne) oder `dB`. |
| **Gruppe** | Gruppierung im VST-UI, z. B. `Pitch`, `Texture`, `Latent`. |
| **Neutone-Slot** | Drag & Drop: Zuordnung zu einem der 4 Neutone-Slots (`null` = nur Custom VST/API). |

**Standard-Knöpfe je Stufe (Vorschlag):**

| Stufe | Vorgeschlagene Inferenz-Parameter |
|---|---|
| `standard` | `Pitch Shift` (−24…+24 st), `Loudness` (−20…+20 dB), `Noise Level` (0–1), `Reverb Mix` (0–1) |
| `component` | `Harmonic Blend`, `Noise Blend`, `Reverb Mix`, `Attack`, `Release`, `Output Gain` |
| `hacks` (FM) | `FM Depth`, `FM Ratio`, `Mod Waveform`, `Feedback`, `Noise Level`, `Output Gain` |
| `engine/sinusoidal` | `Inharmonicity`, `Spectral Spread`, `Partial Density`, `Brightness` |
| `engine/combsub` | `Formant Shift`, `Brightness`, `Vowel`, `Roughness` |
| `engine/newt` | `Tone Character`, `Saturation`, `MLP Layer Bias`, `Odd Harmonics` |
| `advanced/VAE` | `Timbre Z1 … ZN` (die Top-Latent-Dimensionen), `Pitch Shift`, `Loudness` |
| `advanced/Poly` | `Voice Balance`, `Detune`, `Voice Spread`, `Unison Width` |
| `advanced/VC` | `Style Transfer`, `Formant Scale`, `Breathiness`, `Speaker Blend` |

**Tipp für den Export:** Die **praktische Obergrenze** pro Knopf liegt bei 8 –
darüber helfen Gruppierung oder VST-interne Presets. Nutze für
VAE-/Poly-Modelle den **Custom-VST-Export** (bis 16 Parameter); nur 4 davon
lassen sich in einem **Neutone FX**-Export abbilden.

---

## Übersicht: Schnell-Referenz des Trainingsablaufs

| Schritt | Ansicht (Sidebar) | Aktion |
|---|---|---|
| 1 | Dataset & Preprocessing → Upload & Ingestion | Audio-Dateien hochladen |
| 2 | Dataset & Preprocessing → Preprocessing | Merkmale (F0 + Loudness) extrahieren |
| 3 | Model Architecture → Training Config | Wizard: Tier, Qualität, Zielmodus |
| 4 | Model Architecture → Training Config | Tabs anpassen, **▶ Start Training** |
| 5 | Training & Monitor → Training Dashboard | TensorBoard, Stop/Resume, Preset speichern |
| 6 | Inference & Export | Playground testen, Parameter-Builder, Export |