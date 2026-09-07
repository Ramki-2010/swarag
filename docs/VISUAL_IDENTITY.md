# Swaragam — Visual Identity

**Purpose.** This document is the authoritative home for Swaragam's visual
identity decisions. It records the reasoning behind the committed Phase A assets;
it is documentation, **not** an ADR, because no architectural decision was made.

It records only what was established during the Phase A work. Where something was
deferred rather than settled, it says so.

---

## 1. Phase A assets

| Asset | Committed |
|---|---|
| `docs/assets/swaragam-motif-light.svg` | `3876fe3` (2026-09-06) |
| `docs/assets/swaragam-motif-dark.svg` | `3876fe3` (2026-09-06) |

Both are 640x120, hand-authored, with no gradients, no raster data, no scripts
and no external references. They are surfaced in `README.md` through a
theme-aware `<picture>` block, integrated in `e66f916` (2026-09-06).

---

## 2. Approved palette

Five colours. This is a **system**: not every colour appears in every asset.

| Name | Hex |
|---|---|
| Kumkum Red | `#7A1F2B` |
| Sandal Ivory | `#F4EDE1` |
| Temple Gold | `#C9A227` |
| Dark Brass | `#8B6914` |
| Deep Brown | `#5C3A21` |

## 3. Semantic colour roles

| Colour | Role |
|---|---|
| Deep Brown | Structural geometry — the string, the overtone partials, the calibrated baseline |
| Kumkum Red | **The jivari arc only.** One accent, on the one element that carries the meaning |
| Temple Gold | Swara labels, where contrast permits |
| Sandal Ivory | Light-variant ground; carries the structural geometry in the dark variant |
| Dark Brass | **Withheld from the primary motif**, reserved for later asset families. It sits adjacent to Temple Gold, and using both would dilute the single gold accent |

Colour carries meaning, not decoration. The accent's scarcity is what makes it
read as significant.

---

## 4. Motif concept

**Jivari + calibrated baseline.** A taut string enters from the left, meets a
shallow jivari bridge, and beyond the point of contact resolves into spectral
partials and then into swara notation.

The jivari is a real mechanism: on a tanpura the string grazes a flat, near-
parabolic bridge at a tangential angle, and the repeated micro-contacts excite a
cascade of overtones. One pitch becomes a spectrum. The bridge is therefore an
**operator**, which is why the mark can show a transformation rather than place
an instrument beside a waveform.

**The mark is deliberately not:**

- a generic waveform or audio-visualiser graphic;
- an instrument silhouette;
- radial, circular or mandala geometry;
- gradient-filled;
- ornamental.

**It is:** restrained, linear and horizontal, and its geometry is derived from
the repository's own material where applicable — the notation sample below comes
from the project's swara vocabulary, not from generic solfège.

### Geometry as committed

Recorded so the mark is reconstructible, and so later revisions are deliberate.

- **Jivari arc** — `M 240 68 Q 292.5 56 345 62`. This is the approved
  240..380 quadratic Bezier truncated by a de Casteljau split at `t = 0.75`. The
  curve still passes through `(310, 60)`, tangent to the string at the crown, and
  the parent curvature is `8/140 = 5.71%`. Shallowness is what keeps it reading
  as a bridge rather than a swoosh.
- **Overtone partials** — seven strokes, irregular vertical spacing, non-monotonic
  lengths `46 / 70 / 30 / 74 / 62 / 24 / 56`. Left origins fan from the contact
  point as `x = 352 + 0.55 * |y - 60|`, so partials nearest the axis begin closest
  to it. The odd count, the irregular spacing and the absent vertical axis are
  what prevent an EQ-bar reading; the shortened longest strokes are what prevent a
  ruled-text reading.
- **Calibrated baseline** — restrained five-graduation version.

---

## 5. Approved notation sample

```
S · R2 · G3 · M2
```

A **neutral sample** drawn from the repository's own swara vocabulary
(`scripts/sandbox_absent_swara_v2.py`), where each swara is defined as a bin range
in the 72-bin PCD. It denotes no raga and no phrase, and is deliberately not tied
to any open research gate.

---

## 6. Typography

- **Live `<text>`**, not outlined paths, so the SVG source stays readable and
  hand-editable.
- Conservative serif fallback stack: `Georgia, 'Times New Roman', Times, serif`.
- **No outlining** unless an actual rendering problem is demonstrated.
- Latin characters plus numeric swara variants, which require no embedded font.

---

## 7. Accessibility and rendering decisions

Contrast ratios below are computed against the WCAG relative-luminance formula.
The minimum for non-text graphical objects is 3.0:1; for text, 4.5:1.

**Dark variant — Kumkum Red arc with a Sandal Ivory underlay.** Kumkum Red
measures **1.85:1** against GitHub's dark canvas (`#0d1117`), below the graphical
minimum. Rather than swap the semantic role or introduce a new colour, the arc is
drawn twice: a Sandal Ivory stroke beneath (**16.26:1**) carries the *form*, and
Kumkum Red on top carries the *meaning*. Both colours are from the approved five.

**Light variant — swara labels in Deep Brown, not Temple Gold.** Temple Gold
measures **2.08:1** on Sandal Ivory, below the text minimum. Deep Brown measures
**8.67:1** and is used instead. Temple Gold remains the label colour in the dark
variant, where it measures **7.82:1**.

A consequence, recorded rather than hidden: **Temple Gold does not appear in the
light variant at all.** That follows from the contrast decision and is accepted.

**Theme handling.** GitHub serves SVGs as images, so they are style-isolated and
cannot inherit a page colour. The two variants are therefore separate files,
selected by `<picture>` and `prefers-color-scheme`.

---

## 8. Originality and collision review

A **targeted design-collision review** was performed before implementation,
covering jivari/tanpura-inspired marks, Indian-classical-music identities,
music-technology logos, and audio/DSP research identities. The nearest
institutional neighbours were inspected directly:

- **CompMusic** — a multicoloured radial starburst mandala.
- **Dunya** — a solid amber-to-yellow radial-gradient sphere.

Both are circular, radial and full-spectrum. The differentiation established is
**structural, not incidental**: Swaragam's mark is linear and horizontal, uses
three inks, is monochrome-capable by construction, carries no gradient, no radial
geometry, no instrument silhouette and no ornament.

**This was a design-collision check, not legal trademark clearance**, and it was
targeted rather than exhaustive. It does not establish originality as a legal
matter.

---

## 9. Deferred

- **Notation script.** Latin characters with numeric swara variants are the
  **current approved presentation**. The question of **Indic-script notation is
  deferred** to separate future research and design work. This is a deferral, not
  a rejection.
- **Phase B — pending, not started:**
  - compact 64x64 mark;
  - monochrome variant.

---

## 10. Governance

- **This document is the authoritative home for visual-identity decisions.**
  If it and any other document disagree, this one is correct on visual identity.
- `README.md` **surfaces** the visual identity. It is not the decision record and
  must not become one.
- The SVG sources are **implementation artifacts and evidence**, not the decision
  record. Their comments explain what the geometry is; the reasoning lives here.
- Changing an approved colour, role, or the motif concept is a decision, not an
  edit. Record it here.
