# Vendor API Notices

Checked: 2026-06-14

Cockpit Guardian should collect vendor information in three levels:

- Safe now: Windows installed-app detection, running process detection, HID/USB/PnP
  metadata, joystick order, and OpenXR runtime metadata where applicable.
- SDK/API candidate: only when the vendor publishes an SDK/API or clearly offers
  access through an official request path.
- Not safe yet: scraping private app protocols or undocumented config formats.

## Summary

| Vendor app | API / notice status | Recoverable information now |
| --- | --- | --- |
| Pimax Play | Pimax publishes Platform/XR SDKs for VR app integration. The checked docs do not expose a local Pimax Play hardware/config backup API. | Installed app, running process/service, OpenXR runtime, headset USB/PnP data. |
| Meta Quest Link / Oculus | Meta publishes OpenXR SDK resources and Oculus Debug Tool documentation. These are VR runtime/developer tools, not a full Quest Link profile-backup API. | Installed app, Oculus services/processes, OpenXR runtime, Debug Tool location, headset USB/PnP data. |
| Fanatec App / FanaLab | Fanatec SDK is available by request through Fanatec support. | Installed app, running process, Fanatec HID/USB devices; SDK evaluation requires approval. |
| SimPro Manager | Official Simagic docs describe SimPro Manager, device status, local/cloud saves, firmware, and telemetry support. No public local API was found. | Installed app, running process, Simagic HID/USB devices, config/log discovery later if schemas are clear. |
| MOZA Pit House | MOZA publishes an SDK page and support forum area. | Installed app, running process, MOZA HID/USB devices; SDK is a likely integration candidate. |
| Simucube Tuner | Simucube sc-api is public, alpha-stage, C++17, Windows-only, and intended for devices/Tuner information plus telemetry/FFB effects. | Installed app, running process, Simucube HID/USB devices; sc-api is the strongest candidate for deeper data. |
| VNM Config / VNM Sim Center | Official download pages provide VNM UI and firmware tools. No general public local API was found. | Installed app, running process, VNM HID/USB devices. |
| VRS Wheel Tool | VRS documents the Wheel Tool and notes standard Windows USB driver usage. No public DFP API was found. | Installed app, running process, VRS HID/USB devices. |
| Thrustmaster / T.A.R.G.E.T | T.A.R.G.E.T is a scripting/configuration environment with DirectX/virtual device tooling. It is not a cockpit telemetry API. | Installed app, running process, Thrustmaster HID/USB/DirectInput devices. |
| PXN Racing / PXN Wheel | PXN tools and PXN Wheel app expose user adjustments, local storage, and testing. No public PC API was found. | Installed app, running process, PXN HID/USB devices. |
| CONSPIT Link | CONSPIT docs describe CONSPIT Link 2.0, configs, export/import, firmware updates, one-click game configuration, and telemetry compatibility. No public API was found. | Installed app, running process, CONSPIT HID/USB devices; documented config export/import may become useful. |

## Implementation Direction

1. Keep vendor software detection lightweight by default: installed programs and
   running processes.
2. Use HID/USB/PnP metadata as the baseline for cockpit restoration after a
   Windows reinstall.
3. Use OpenXR registry/runtime detection for Pimax Play and Meta Quest Link.
4. Prioritize SDK exploration in this order: Simucube sc-api, MOZA SDK, Fanatec
   SDK request path.
5. Treat SimPro Manager, VNM, VRS, Thrustmaster, PXN, and CONSPIT as
   Windows/HID/USB integrations until an official local API is found.
6. Only add config-file import/export when the file location and schema are
   documented or proven stable enough to restore safely.

## Sources Checked

- Pimax SDK: https://developer.pimax.com/sdk/
- Pimax Native Platform SDK: https://developer.pimax.com/document/sdk/native/native-platform-sdk.html
- Meta OpenXR SDK: https://developers.meta.com/horizon/downloads/package/oculus-openxr-mobile-sdk/
- Oculus Debug Tool: https://developers.meta.com/horizon/documentation/native/pc/dg-debug-tool/
- Fanatec SDK request: https://help.fanatec.com/hc/en-us/articles/44194638149777-I-want-to-request-access-to-Fanatec-s-SDK
- SIMAGIC download center: https://simagic.com/pages/download-center
- SIMAGIC SimPro Manager user guide: https://simagic.com/blogs/announcement/simagic-latest-driver-simpro-manager-user-guide
- MOZA SDK: https://mozaracing.com/pages/sdk
- MOZA SDK support forum: https://support.mozaracing.com/support/discussions/forums/70000317671
- Simucube Link API: https://simucube.com/en-us/simucube-link-api-sc-api/
- Simucube sc-api GitHub: https://github.com/Simucube/sc-api
- VNM software downloads: https://vnmsimulation.com/download/
- VNM Direct Drive manual repository: https://github.com/vnmsimulation/vnm_direct_drive/blob/master/Configuration%20Manual/VNM%20Direct%20Drive%20User%20Manual.pdf
- VRS DirectForce Pro FAQ: https://virtualracingschool.com/academy/hardware/vrs-directforce-pro-faq/
- VRS DirectForce Pro settings: https://virtualracingschool.com/academy/hardware/vrs-directforce-pro-wheel-base-settings-various-racing-titles/
- Thrustmaster support: https://support.thrustmaster.com/en/
- Thrustmaster T.A.R.G.E.T Script Editor Basics: https://ts.thrustmaster.com/download/accessories/pc/hotas/software/TARGET/TARGET_Script_Editor_Basics_v1.5_ENG.pdf
- PXN tools: https://www.e-pxn.com/support/tools
- PXN Wheel app: https://play.google.com/store/apps/details?hl=en_US&id=com.pxn.driving
- CONSPIT downloads: https://conspit.com/download
- CONSPIT Ares Series Function Guide: https://oss.conspit.com/video/2025/6/6/1749194528494.pdf
