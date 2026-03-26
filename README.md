# PocketOP Database

Public lens and camera database for [PocketOP](https://github.com/directimages/PocketOP), an iOS app for broadcast professionals.

This repository contains the JSON data files that the PocketOP app fetches at runtime. Updates to these files are delivered to users without requiring an app update.

## Files

| File | Description |
|---|---|
| `lenses.json` | Broadcast lenses (Canon, Fujinon, Angénieux, Leica) |
| `ptz_cameras.json` | PTZ cameras (Canon, Sony, Panasonic, JVC) |
| `devices.json` | Supported iPhone models with camera specifications |

## Delivery

Files are served via [jsDelivr](https://www.jsdelivr.com/) CDN:
```
https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main/lenses.json
https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main/ptz_cameras.json
https://cdn.jsdelivr.net/gh/directimages/PocketOP-Database@main/devices.json
```

## Versioning

Each file contains a `version` field using semantic versioning:

- **PATCH** (x.x.1): data correction, HFOV adjustment, typo fix
- **MINOR** (x.1.0): new lens, PTZ camera, or device added
- **MAJOR** (1.0.0): structural change to the JSON schema

## License

This data is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE).
```

**LICENSE**
```
Creative Commons Attribution 4.0 International (CC BY 4.0)

Copyright (c) 2026 Martijn — directimages

You are free to:
  Share — copy and redistribute the material in any medium or format
  Adapt — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
  Attribution — You must give appropriate credit, provide a link to the license,
  and indicate if changes were made.

Full license text: https://creativecommons.org/licenses/by/4.0/legalcode
```

**.gitignore**
```
# macOS
.DS_Store
.AppleDouble
.LSOverride

# Editor
.vscode/
*.swp
*.swo

# Temporary
*.tmp
*.bak
