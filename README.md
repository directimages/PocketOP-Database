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

Files are delivered to the PocketOP app via CDN at runtime.

## Versioning

Each file contains a `version` field using semantic versioning:

- **PATCH** (x.x.1): data correction, HFOV adjustment, typo fix
- **MINOR** (x.1.0): new lens, PTZ camera, or device added
- **MAJOR** (1.0.0): structural change to the JSON schema

## License

This data is licensed under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE). Commercial use requires written permission from Direct Images.
