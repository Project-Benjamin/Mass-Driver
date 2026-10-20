# Rico NPC portrait references

The user's requirement is to interpret the actual NPC sprite's face and upper
chest. A role such as guard, worker, or doctor is not a sufficient art brief.

Before generating or replacing a portrait, trace the speaking actor in the
current built scene to its native actor bank, sprite atlas, selected palette,
and any tint or scaling applied by the script. Inspect both the atlas and a
legible head/upper-body crop. Record those references in the portrait source's
provenance entry. Use the retail portrait sheet for drawing style only.

Preserve visible headgear, eyewear, hair silhouette, face exposure, costume
colors, collar and upper-chest details. Keep ambiguous small details simple
and identify interpretations as such. User corrections take priority over a
previous interpretation of low-resolution pixels.

Suzarn is an adult woman. The user approved the ribbed olive-gold helmet and
goggles and explicitly requested an uncovered nose, mouth and chin. Retain
the separate dark bomb collar with spaced rectangular lights. Native field
218 bank0 palette0 torso pixels show an open charcoal-gray jacket, exposed
tan upper chest, and a horizontal cream/beige inner-top band. Interpret that
band as a tube top; no straps are visible in these front torso parts. Leave
bare skin between the collar and the top, and frame enough upper chest for
the garment to remain visible at 64x64. Do not replace this with a closed
high-neck uniform. Exact native crops and palette evidence are recorded in
`work/rico_suzarn_v8/native_reference.json` and `reference_notes.md`.
The infirmary guard's actual palette0 has blue clothing and pale goggles;
its alternative green palette is not the installed actor's appearance.

When several NPC labels share one sprite identity, use consistent portrait
features. When the sprite itself is a placeholder for the wrong named actor,
fix or document the mapping instead of inventing an unrelated portrait.

Review the generated image and the decoded native 64x64 TIM before packaging.
Store the final prompt, references and image hashes with the project. Rebuild
and explicitly activate the new release so Play Rico does not point at a
stale package. Build and byte checks do not establish gameplay acceptance.
