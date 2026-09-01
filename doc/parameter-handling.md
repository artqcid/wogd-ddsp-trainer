---
type: concept
status: draft
generated:
  by: ARCHITECT_Openrouter
  at: 2026-09-01
description: Input-Parameter-Handling für alle Modell-Trainings-Variationen — Zwei-Schicht-Modell, Neutone-Constraint, Custom-VST-16, GUI-Design
stale_after: 2027-06-01
tags: [parameters, neutone, export, vst, inference, gui, model-tiers]
---

# Input Parameter Handling

_Vollständige Analyse der Input-Parameter-Dynamik für alle Modell-Trainings-Variationen.
Betrifft: Modell-Export, Neutone-VST-Constraint, Custom-VST (16 Parameter),
GUI-Design des Parameter-Builders, Parameternamen-Customization._

_Verwandte Dokumente: [`architecture.md`](./architecture.md) (Tier-System, Export-Endpunkte),
[`ui-requirements.md`](./ui-requirements.md) (ModelExportView, ModelParameterBuilder),
[`plan.md`](./plan.md) (Milestones M3/M6/M14)._

---

## 1. Das Zwei-Schichten-Modell (Fundament)

Die wichtigste konzeptuelle Trennung: **Trainings-Konfigurationsparameter** und
**Inferenz-Laufzeitparameter** sind grundverschieden und dürfen nicht verwechselt werden.

### Schicht 1 — Trainings-Konfigurationsparameter (Architecture Params)

Diese Parameter definieren die **Modellarchitektur** und werden beim Training **eingebettet**.
Sie erscheinen nicht als VST-Knöpfe; sie sind nach dem Training unveränderlich im Checkpoint.

Beispiele: `hidden_size`, `n_harmonics`, `n_filter_banks`, `engine`, `use_latent`,
`latent_dim`, `n_voices`, `fm_depth_initial`, `wavetable_type`, `use_content_encoder`.

Quelle: `server/presets.py` (`PARAM_KEYS`, `VARIANT_KEYS`, `ENGINE_KEYS`, `ADVANCED_KEYS`),
verwaltet über die Training-Config-UI (`TrainingConfigView` + Tier-Tabs).

### Schicht 2 — Inferenz-Laufzeitparameter (Runtime Params)

Diese Parameter **steuern das Modell zur Laufzeit** — pro Audiobuffer, in Echtzeit.
Sie sind die **VST-Knöpfe** (Neutone oder Custom-VST) und die Schieberegler
in der Inference Playground-UI.

Beispiele: `pitch_shift`, `loudness_shift`, `harmonic_blend`, `latent_z1`,
`fm_depth`, `tone_character`, `formant_shift`.

Quelle: exportiert via `get_neutone_parameters()` (Neutone SDK) oder über das
Custom-VST-Interface (siehe Abschnitt 4).

**Regel:** Schicht-1-Parameter erscheinen NIEMALS als VST-Knöpfe. Schicht-2-Parameter
können NICHT die Modellarchitektur ändern, nur das Modellverhalten innerhalb der
trainierten Grenzen steuern.

---

## 2. Neutone VST — Hard-Limit-Analyse (4 Parameter)

### Fakten aus dem Neutone SDK (v1.5.2, verifiziert 2026-09-01)

```
neutone_sdk/constants.py:
    MAX_N_PARAMS = 4                      # Hard limit für Neutone FX Plugin
    NEUTONE_GEN_N_NUMERICAL_PARAMS = 4    # Neutone Gen: ebenfalls 4 numerische
    NEUTONE_GEN_N_TEXT_PARAMS = 1         # + 1 Textfeld
    NEUTONE_GEN_N_TOKENS_PARAMS = 1       # + 1 Token-Stream

neutone_sdk/core.py:
    assert self.n_neutone_parameters <= self.MAX_N_PARAMS
    # → SDK-seitiger Assert, bricht den Export mit Fehler ab
```

### Was bedeutet das konkret

- **Neutone FX (Realtime-Plugin):** exakt ≤ 4 Parameter. Keine Ausnahme. Das Plugin
  rendert physisch 4 Knöpfe in der DAW; ein Modell mit 5 Parametern kann nicht
  in das `.nm`-Format exportiert werden.
- **Neutone Gen (Non-Realtime):** 4 numerische + 1 Text + 1 Token-Stream = 6 total.
  Für generative, nicht-echtzeittaugliche Modelle (z. B. LoopGAN, Stable Audio).
- **Parameternamen:** frei wählbar (`name`-Feld in `NeutoneParameter`). Das Plugin
  zeigt den Namen als Tooltip. Namen werden in den Modell-Metadaten gespeichert
  und können beim Wrapper-Export gesetzt werden.
- **Parametertypen:** `ContinuousNeutoneParameter` (float [0,1] mit min/max-Mapping),
  `CategoricalNeutoneParameter` (diskrete Auswahl ≤ 20 Labels),
  `TextNeutoneParameter` (Freitext), `DiscreteTokensNeutoneParameter` (Token-Liste).

### Konsequenz für unsere Standard-Modelle

Standard-Modelle werden **immer mit genau 4 Inferenz-Parametern** exportiert.
Die 4 Slots sind durch das Plugin vorgegeben; wir befüllen sie mit sinnvollen Defaults
pro Modell-Tier. Der Benutzer kann die Parameternamen und Defaults in der Export-UI
überschreiben, bevor das `.nm`-File erzeugt wird.

---

## 3. Custom VST — 16-Parameter-Erweiterung

Da ein eigenes VST entwickelt wird, das bis zu **16 Inferenz-Parameter** verarbeiten
kann, ergibt sich folgende Dual-Export-Architektur:

### Export-Pfade (zwei parallele Targets)

```
Checkpoint (.pt)
    │
    ├─► Neutone FX Export (.nm)
    │       └─ max. 4 Parameter (Neutone SDK Hard-Limit)
    │          parameternamen + defaults customizierbar
    │          → WaveformToWaveformBase wrapper
    │
    └─► Custom VST Export (.pt / TorchScript)
            └─ max. 16 Parameter (Custom-VST-Interface)
               vollständige Parameter-Suite pro Tier
               parameternamen, beschreibungen, min/max/defaults customizierbar
               → eigener Wrapper (analog zu Neutone SDK, eigenes Interface)
```

### Parameter-Manifest (Custom VST)

Das Custom-VST-Interface liest ein **Parameter-Manifest** aus dem Modell-Checkpoint:

```json
{
  "format": "wogd-vst-params",
  "version": "1.0",
  "n_params": 8,
  "params": [
    { "slot": 1, "name": "Pitch Shift",    "description": "F0 offset in semitones",
      "type": "continuous", "min": -24.0, "max": 24.0, "default": 0.0 },
    { "slot": 2, "name": "Loudness",       "description": "Output loudness offset dB",
      "type": "continuous", "min": -20.0, "max": 20.0, "default": 0.0 },
    { "slot": 3, "name": "Harmonic Blend", "description": "Tonal vs. Noise balance",
      "type": "continuous", "min": 0.0,   "max": 1.0,  "default": 0.5 },
    ...
  ]
}
```

Das Manifest wird beim Checkpoint-Speichern unter `state["param_manifest"]` eingebettet
und beim Export in die TorchScript-Metadaten übertragen.

### Sinnvolle Parameterzahl pro Tier

| Tier          | Neutone FX | Custom VST (empfohlen) | Custom VST (max) | Begründung |
|---------------|-----------|------------------------|-----------------|------------|
| `standard`    | 4         | 4                      | 4               | Kein Mehrwert über 4 |
| `component`   | 4         | 4–6                    | 8               | harmonic/noise blend + extras |
| `hacks`       | 4         | 4–8                    | 12              | je nach aktiven Hack-Flags |
| `engine`      | 4         | 4–6                    | 8               | engine-spezifische Klangfarbe |
| `advanced/VAE`| 4         | 6–10                   | 16              | latente Dimensionen steuerbar |
| `advanced/Poly`| 4        | 4–8                    | 12              | Stimmen-Balance + Klang |
| `advanced/VC` | 4         | 4–6                    | 8               | Speaker-Style-Transfer |

**Kognitiver Richtwert:** Bis 8 Parameter sind intuitiv bedienbar. 9–16 Parameter
erfordern eine Gruppierung oder Preset-Unterstützung im VST-UI. Über 16 hinaus
empfiehlt sich eine Patch-basierte Steuerung statt Einzelknöpfe.

---

## 4. Standard-Modell — Parameternamen und Defaults

### Automatische Defaults pro Tier (werden vom Trainer vorgeschlagen)

#### `standard` (4 Parameter, fix)
| Slot | Default-Name      | Typ        | Min   | Max  | Default | Beschreibung |
|------|-------------------|------------|-------|------|---------|--------------|
| 1    | `Pitch Shift`     | continuous | −24.0 | +24  | 0.0     | F0-Verschiebung in Halbtönen |
| 2    | `Loudness`        | continuous | −20.0 | +20  | 0.0     | Lautstärke-Offset dB |
| 3    | `Noise Level`     | continuous |   0.0 |  1.0 | 0.5     | Anteil FilteredNoise am Ausgang |
| 4    | `Reverb Mix`      | continuous |   0.0 |  1.0 | 0.3     | Dry/Wet-Verhältnis Reverb |

#### `component` (4 Neutone / 6 Custom-VST)
| Slot | Default-Name      | Typ        | Min   | Max  | Default | Neutone? |
|------|-------------------|------------|-------|------|---------|----------|
| 1    | `Pitch Shift`     | continuous | −24   | +24  | 0.0     | ✓        |
| 2    | `Loudness`        | continuous | −20   | +20  | 0.0     | ✓        |
| 3    | `Harmonic Blend`  | continuous |  0.0  |  1.0 | 0.5     | ✓        |
| 4    | `Noise Blend`     | continuous |  0.0  |  1.0 | 0.5     | ✓        |
| 5    | `Reverb Mix`      | continuous |  0.0  |  1.0 | 0.3     | Custom   |
| 6    | `Spectral Spread` | continuous |  0.0  |  1.0 | 0.5     | Custom   |

#### `hacks` — abhängig von aktiven DDSPVariant-Flags

Das Trainer-System wählt den Parametersatz basierend darauf, welche Hacks beim
Training aktiviert waren. Beispiele:

**FM-Hack aktiv:**
| Slot | Name          | Neutone? |
|------|---------------|----------|
| 1    | `Pitch Shift` | ✓        |
| 2    | `Loudness`    | ✓        |
| 3    | `FM Depth`    | ✓        |
| 4    | `FM Ratio`    | ✓        |
| 5    | `LFO Rate`    | Custom   |
| 6    | `LFO Depth`   | Custom   |

**Wavetable-Hack aktiv:**
| Slot | Name              | Neutone? |
|------|-------------------|----------|
| 1    | `Pitch Shift`     | ✓        |
| 2    | `Loudness`        | ✓        |
| 3    | `Wavetable Pos`   | ✓        |
| 4    | `Noise Level`     | ✓        |
| 5    | `Phase Distort`   | Custom   |
| 6    | `Harmonic Dirt`   | Custom   |

**Phase-Distortion-Hack aktiv:**
| Slot | Name              | Neutone? |
|------|-------------------|----------|
| 1    | `Pitch Shift`     | ✓        |
| 2    | `Loudness`        | ✓        |
| 3    | `PD Amount`       | ✓        |
| 4    | `Waveshape`       | ✓        |

#### `engine` — abhängig von gewählter Engine

**`harmonic` (Standard-Engine):** identisch zu `standard`.

**`sinusoidal`:**
| Slot | Name               | Neutone? |
|------|--------------------|----------|
| 1    | `Pitch Shift`      | ✓        |
| 2    | `Loudness`         | ✓        |
| 3    | `Inharmonicity`    | ✓        |
| 4    | `Spectral Spread`  | ✓        |
| 5    | `Partial Density`  | Custom   |
| 6    | `Brightness`       | Custom   |

**`combsub`:**
| Slot | Name              | Neutone? |
|------|-------------------|----------|
| 1    | `Pitch Shift`     | ✓        |
| 2    | `Loudness`        | ✓        |
| 3    | `Formant Shift`   | ✓        |
| 4    | `Brightness`      | ✓        |
| 5    | `Vowel`           | Custom   |
| 6    | `Roughness`       | Custom   |

**`newt` (NEWT Neural Waveshaping):**
| Slot | Name               | Neutone? |
|------|--------------------|----------|
| 1    | `Pitch Shift`      | ✓        |
| 2    | `Loudness`         | ✓        |
| 3    | `Tone Character`   | ✓        |
| 4    | `Saturation`       | ✓        |
| 5    | `MLP Layer Bias`   | Custom   |
| 6    | `Odd Harmonics`    | Custom   |

#### `advanced` — VAE Latent Space

Dies ist der komplexeste Fall. Der VAE-Encoder erzeugt einen latenten Raum
mit `latent_dim` Dimensionen (Default: 32). Nicht alle Dimensionen sind
gleich wichtig; die relevantesten werden über **PCA-Analyse des Trainings-Datasets**
identifiziert (Top-K nach erklärter Varianz).

| Slot | Name                  | Typ        | Neutone? |
|------|-----------------------|------------|----------|
| 1    | `Pitch Shift`         | continuous | ✓        |
| 2    | `Loudness`            | continuous | ✓        |
| 3    | `Timbre Z1`           | continuous | ✓        |
| 4    | `Timbre Z2`           | continuous | ✓        |
| 5    | `Timbre Z3`           | Custom     |          |
| 6    | `Timbre Z4`           | Custom     |          |
| 7–16 | `Timbre Z5`–`Z14`    | Custom     |          |

**Wichtige Regel für VAE-Exports:** Die per-Dimension-Labels (`Z1`..`ZN`) sind
zunächst generische Platzhalter. Der Trainer kann nach dem Training eine
**Latent-Dimension-Beschriftung** durchführen: jede Dimension wird durch
gezielte Extremwert-Synthese interpretiert (z. B. Z1 = „Rauigkeit", Z2 = „Helligkeit")
und der Benutzer vergibt manuelle Namen. Diese Namen fließen in das Parameter-Manifest
ein und erscheinen im VST-UI.

#### `advanced` — PolyDDSP (N Stimmen)
| Slot | Name               | Neutone? |
|------|--------------------|----------|
| 1    | `Pitch Shift`      | ✓        |
| 2    | `Loudness`         | ✓        |
| 3    | `Voice Balance`    | ✓ (Blend V1/V2) |
| 4    | `Detune`           | ✓        |
| 5    | `Voice Spread`     | Custom   |
| 6    | `Unison Width`     | Custom   |

#### `advanced` — Voice Conversion (HuBERT/ContentVec)
| Slot | Name               | Neutone? |
|------|--------------------|----------|
| 1    | `Pitch Shift`      | ✓        |
| 2    | `Loudness`         | ✓        |
| 3    | `Style Transfer`   | ✓ (0=source, 1=target) |
| 4    | `Formant Scale`    | ✓        |
| 5    | `Breathiness`      | Custom   |
| 6    | `Speaker Blend`    | Custom   |

---

## 5. Parameternamen-Customization

### Standard-Modelle

Die 4 Neutone-Parameter-Namen werden vom Modell-Tier automatisch vorgeschlagen
(Defaults aus den Tabellen oben). Der Benutzer kann sie im **Parameter Editor**
in der `ModelExportView` überschreiben, bevor der Export ausgeführt wird:

- **Name:** max. 30 Zeichen (Neutone-Limit für UI-Anzeige)
- **Beschreibung:** max. 150 Zeichen (Tooltip in der DAW)
- **Default-Wert:** innerhalb [min, max]
- **Typ:** continuous oder categorical (mit eigenen Labels)

Änderungen werden im Checkpoint-Manifest gespeichert und beim Re-Export
wiederverwendet. Sie ändern die Modellgewichte nicht.

### Experimentelle Modelle (Custom VST)

Für das Custom-VST können alle ≤ 16 Parameter individuell benannt werden.
Zusätzlich zu Name und Beschreibung:

- **Einheit/Skala-Hint:** z. B. „Halbtöne", „dB", „[0–1]", „Prozent"
  (wird im VST-UI als Label-Suffix angezeigt)
- **Mapping-Kurve:** `linear` (default), `logarithmic` (für Frequenz/VRAM-ähnliche
  Größen), `exponential` (für Verstärkung/Pegel-ähnliche Größen)
- **Gruppen-Tag:** optionale Gruppierung für das VST-UI
  (z. B. `"Pitch"`, `"Texture"`, `"Latent"`)
- **Neutone-Export-Slot:** welcher der 4 Neutone-Slots dieser Parameter belegt
  (oder `null` = nur Custom-VST, nicht in Neutone-Export)

---

## 6. GUI-Design — `ModelParameterBuilder` Komponente

### Übersicht

Ein neues Vue-3-Komponent `ModelParameterBuilder.vue` in der `ModelExportView`.
Es ist der einzige Ort, an dem Schicht-2-Parameter (Inferenz-Laufzeit) konfiguriert
werden — getrennt vom Training-Config-Flow.

### Dual-Mode: Standard vs. Erweiterter Modus

```
┌─────────────────────────────────────────────────────────────────┐
│  PARAMETER EDITOR                               [Standard] [+]  │
│                                                                  │
│  NEUTONE FX (max 4)                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Knob 1  │ │  Knob 2  │ │  Knob 3  │ │  Knob 4  │          │
│  │Pitch Shft│ │ Loudness │ │Harm Blend│ │Noise Blnd│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  [Name ✎] [Name ✎] [Name ✎] [Name ✎]                          │
│                                                                  │
│  CUSTOM VST (bis 16)     ← nur sichtbar wenn Tier ≥ component  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                │
│  │ P 5  │ │ P 6  │ │ P 7  │ │ P 8  │ │ + Add│                │
│  │Reverb│ │Spctrl│ │      │ │      │ │      │                │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                │
│                                                                  │
│  [Export → Neutone FX (.nm)]  [Export → Custom VST (.pt)]      │
└─────────────────────────────────────────────────────────────────┘
```

### Parameter-Karte (einzelne Parametereinheit)

Jede Parameterposition wird als Karte dargestellt:

```
┌────────────────────────────────────────┐
│  ⠿  [drag]   P3              [✕ entf.] │
│                                         │
│  Name:        [Harmonic Blend        ]  │
│  Beschreibung:[Tonal vs. Noise blend ]  │
│  Typ:         [● continuous ○ categ. ]  │
│  Min:  [-1.0]  Max: [1.0]  Default: [0] │
│  Mapping: [● linear ○ log ○ exp      ]  │
│  Einheit: [                          ]  │
│                                         │
│  Neutone-Slot: [Slot 3 ▾]  [Auto]      │
└────────────────────────────────────────┘
```

### Dynamische Anpassung je nach Tier

- **`standard`:** 4 Karten, keine Add-Schaltfläche, kein Custom-VST-Abschnitt.
  Names sind editierbar, Slots 1–4 sind fix zugewiesen.
- **`component` / `hacks` / `engine`:** 4 Neutone-Karten + Custom-VST-Abschnitt
  mit automatisch vorgeschlagenen Parametern (5–8). Add-Schaltfläche verfügbar.
- **`advanced`:** vollständiger Builder. Neutone-Abschnitt zeigt 4 Karten mit
  Slot-Zuweisungslogik. Custom-VST-Abschnitt zeigt alle weiteren Parameter
  bis zu 16. Bei VAE-Modellen: Latent-Dimensionen erscheinen als generische
  Platzhalter mit „Beschriften"-Button.

### Neutone-Slot-Zuweisungslogik (Drag & Drop)

Wenn ein Benutzer im Custom-VST-Bereich mehr als 4 Parameter definiert hat,
kann er beliebig per Drag & Drop entscheiden, welche 4 in den Neutone-Export
kommen:

```
ALLE PARAMETER (8 definiert)          NEUTONE FX SLOTS (4)
┌───────────────────────────┐         ┌──┐ ┌──┐ ┌──┐ ┌──┐
│ ⊕ Pitch Shift   [→ Slot1] │ ──drag─►│K1│ │K2│ │K3│ │K4│
│ ⊕ Loudness      [→ Slot2] │         └──┘ └──┘ └──┘ └──┘
│ ⊕ Harmonic Bld  [→ Slot3] │
│ ⊕ Noise Blend   [→ Slot4] │  ← Diese 4 → Neutone
│ ○ Reverb Mix    [API only]│
│ ○ Spectral Spr  [API only]│  ← Diese → nur Custom VST + API
│ ○ Timbre Z3     [API only]│
│ ○ Timbre Z4     [API only]│
└───────────────────────────┘
```

---

## 7. Export-Decision-Tree

```
Checkpoint vorhanden?
        │
        ▼
Welcher Export-Pfad?
        │
        ├─► Neutone FX (.nm)
        │       ├─ Wähle 4 Parameter (aus Parameter-Builder)
        │       ├─ Validiere: alle Namen ≤ 30 Zeichen
        │       ├─ Wähle NeutoneParameter-Typen
        │       ├─ Erstelle WaveformToWaveformBase-Wrapper
        │       └─ save_neutone_model() → model.nm
        │
        ├─► Custom VST (.pt / TorchScript)
        │       ├─ Alle ≤ 16 Parameter aus Builder
        │       ├─ Schreibe param_manifest in Checkpoint-State
        │       ├─ torch.jit.script(wrapper) → model.pt
        │       └─ Custom-VST liest manifest beim Laden
        │
        └─► API / Offline (.pt)
                ├─ Alle Parameter aus Builder
                ├─ Keine Slot-Beschränkung
                ├─ Parameter als JSON-Body im POST /inference/synthesize
                └─ Checkpoint unverändert, kein separater Wrapper
```

### REST-Erweiterung: `GET /api/models/{run_id}/{checkpoint}/params`

Neuer Endpunkt (zukünftig), der das Parameter-Manifest eines Checkpoints zurückgibt:

```json
{
  "n_params": 8,
  "neutone_slots": [1, 2, 3, 4],
  "params": [
    { "slot": 1, "name": "Pitch Shift", "type": "continuous",
      "min": -24.0, "max": 24.0, "default": 0.0,
      "neutone_slot": 1, "group": "Pitch" },
    { "slot": 5, "name": "Reverb Mix", "type": "continuous",
      "min": 0.0, "max": 1.0, "default": 0.3,
      "neutone_slot": null, "group": "Effects" }
  ]
}
```

---

## 8. Backend-Repräsentation — `param_manifest` im Checkpoint

### Schema (in `server/tasks.py` / `model/ddsp/model.py`)

```python
@dataclass
class InferenceParam:
    slot: int                    # 1-basiert, 1..16
    name: str                    # max 30 Zeichen
    description: str             # max 150 Zeichen
    type: str                    # "continuous" | "categorical"
    min_value: float
    max_value: float
    default_value: float
    mapping: str                 # "linear" | "log" | "exp"
    unit_hint: str               # z.B. "semitones", "dB", ""
    group: str                   # z.B. "Pitch", "Texture", "Latent"
    neutone_slot: int | None     # 1..4 oder None (Custom/API only)


@dataclass
class ParamManifest:
    format: str = "wogd-vst-params"
    version: str = "1.0"
    params: list[InferenceParam] = field(default_factory=list)

    @property
    def neutone_params(self) -> list[InferenceParam]:
        """Gibt die 4 für Neutone bestimmten Parameter zurück, sortiert nach Slot."""
        return sorted(
            [p for p in self.params if p.neutone_slot is not None],
            key=lambda p: p.neutone_slot
        )

    @property
    def custom_vst_params(self) -> list[InferenceParam]:
        """Gibt alle ≤ 16 Parameter zurück (inkl. Neutone-Slots)."""
        return sorted(self.params, key=lambda p: p.slot)
```

### Einbettung in Checkpoint

```python
# Beim Speichern (train/trainer.py oder server/tasks.py):
state = {
    "model_state_dict": model.state_dict(),
    "model_tier": model_tier,
    "engine": engine,
    # ... weitere Tier-Felder ...
    "param_manifest": manifest.to_dict(),   # NEU
}
torch.save(state, checkpoint_path)
```

Der `param_manifest`-Key wird beim Speichern eines neuen Checkpoints durch den
Trainer leer (mit Tier-Defaults vorbelegt) gesetzt und kann anschließend über
die Export-UI überschrieben werden ohne die Modellgewichte zu verändern.

---

## 9. Tier-Defaults (automatisch generiert, überschreibbar)

Damit der Benutzer nicht bei jedem Export von vorne beginnt, generiert das
Backend beim ersten Aufruf der Export-UI automatisch einen vollständigen
`ParamManifest`-Vorschlag basierend auf dem `model_tier` und aktiven
`DDSPVariant`-Flags:

```python
# server/routes/models.py (zukünftig)
def build_default_manifest(model_tier: str, variant_flags: dict) -> ParamManifest:
    """Generiert einen tier-spezifischen Parameter-Manifest-Vorschlag."""
    if model_tier == "standard":
        return _standard_manifest()
    elif model_tier == "component":
        return _component_manifest()
    elif model_tier == "hacks":
        return _hacks_manifest(variant_flags)
    elif model_tier == "engine":
        return _engine_manifest(variant_flags.get("engine", "harmonic"))
    elif model_tier == "advanced":
        return _advanced_manifest(variant_flags)
    return _standard_manifest()
```

Dieses System stellt sicher:
1. Sofort sinnvolle Defaults ohne Benutzeraufwand
2. Vollständige Überschreibbarkeit pro Modell
3. Persistenz der Anpassungen im Checkpoint für Re-Exporte

---

## 10. Zusammenfassung: Entscheidungsmatrix

| Frage | Antwort |
|-------|---------|
| Standardmodell → wie viele Inferenz-Parameter? | Immer 4 |
| Standard → Parameternamen anpassen? | Ja, im Parameter Builder vor Export |
| Standard → Neutone FX exportierbar? | Ja, direkt (4 ≤ MAX_N_PARAMS) |
| Experimentelles Modell → Neutone FX? | Ja, aber nur 4 der N Parameter werden gemappt |
| Experimentelles Modell → Custom VST? | Ja, bis 16 Parameter |
| Experimentelles Modell → wie viele sinnvoll? | 4–8 (bis 16 für Forschung/VAE) |
| Parameternamen experimental? | Ja, vollständig customizierbar (Name, Einheit, Gruppe, Kurve) |
| Trainings-Config-Params im VST? | Nein, niemals — nur Inferenz-Schicht |
| Wo liegt das Manifest? | `state["param_manifest"]` im Checkpoint |
| GUI-Komponente? | `ModelParameterBuilder.vue` in `ModelExportView` |
| Automatische Defaults? | Ja, tier-spezifisch via `build_default_manifest()` |

---

## References

- [`architecture.md`](./architecture.md) — Tier-System, Export-Endpunkte
- [`ui-requirements.md`](./ui-requirements.md) — ModelExportView, Kopplungsregeln
- [`experimental-sdk-hacking.md`](./experimental-sdk-hacking.md) — DDSPVariant-Flags (M8)
- [`experimental-ddsp.md`](./experimental-ddsp.md) — VAE Latent Space (M11)
- [`plan.md`](./plan.md) — Milestones M6 (Export), M14 (Dual-Mode UI)
- Neutone SDK v1.5.2: `constants.py` (`MAX_N_PARAMS = 4`), `core.py` (Assert), `parameter.py`
