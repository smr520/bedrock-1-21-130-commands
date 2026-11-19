# World metadata template

`world-template.level.dat` is a sanitized little-endian Bedrock `level.dat` used only to preserve the complete metadata key set required by Bedrock and NetEase worlds.

The exporter replaces the world name, spawn, game type, command settings, seed and related fields. All chunks and command blocks are generated from the current chain spec; the template does not provide terrain or commands.

## Provenance

- Adapted from `scripts/_template.mcworld` in `yixin-amore/MinecraftBE-Command-Building-Skill`
- Audited commit: `9184e4d36c4df62a8fc4e2be951bd9163dd8196a`
- Upstream license: MIT
- Sanitized fields include `LevelName=projection-template`, `RandomSeed=0`, empty `prid`, zero timestamps and zero spawn.

## Integrity

```text
SHA-256: fed9ce5d3dc1c5fc236288263ffa9b5bd55d8a1b53c46675e5db690324f42c92
Size: 2828 bytes
```

The exporter records this hash in every generated `projection.json`.
