# Galaxy A50 — One UI 9 / Android 17 port (S26 FE system)

Port of the Samsung Galaxy S26 FE system (SM-S741B, Android 17 / One UI 9.0, build `S741BXXS2AZI3`)
to the Galaxy A50 (Exynos 9610, Mali-G72), running on an Android 13 A50 vendor (VNDK 33)
and the 4.14 **Ultimate Kernel A50**.

> This repo is the **port kit**: kernel patch, patch tools, configs and notes.
> It contains **no Samsung firmware or proprietary binaries** — bring your own S26 FE system and A50 vendor.

## Status

| Working | Notes |
|---|---|
| Boot, One UI 9 home, Settings | Smoother than stock A50 |
| Wi-Fi, networking, DNS, BPF | needs kernel LPM-trie backport + tethering APEX patches |
| Bluetooth (on / scan / pair) | `libbluetooth_jni.so` VaultKeeper loop skipped |
| Audio | 32-bit support restored for the A50 32-bit audio HAL |
| Calls / SIM, SD card, USB OTG | sdfat `time_offset` mount option accepted in kernel |
| Camera | Samsung Camera app: own A50 M12 port (see camera/). Vendor camera stack: stock Samsung firmware only (A50 HAL/core/sensor files + A51 Android 13 framework), hash-verified |
| GPU | SkiaGL, Mali-G72 GLES 3.2 |
| Root | APatch |
| Chrome, Play Store (+ self-update), Play Services | GMS in /system, **product partition empty** |

| Not working / untested | |
|---|---|
| Smart View | connects to TV, but black screen: 64-bit WFD vs 32-bit A50 OMX encoder (see below) |
| Mobile data | untested |

## Partition layout

| Partition | Image |
|---|---|
| boot | Ultimate Kernel A50 (`./build_ultimate.sh`), patched with APatch |
| system | S26 FE system, modified (EROFS, lz4hc) |
| vendor | A50 Android 13 vendor + fixes (EROFS) |
| product | **empty** 4 KB EROFS (old product contents break zygote / duplicate GMS) |

## Kernel (4.14) changes — `kernel/mint14_all_changes.patch`

- `kernel/bpf/lpm_trie.c`: backport of upstream 4.16 `trie_get_next_key` (BpfNetMaps needs it; stub returned ENOTSUPP 524)
- `CONFIG_RT_GROUP_SCHED` off + `kernel/sched/rt.c` build fixes
- `fs/sdfat`: accept and ignore `time_offset=%d` (USB OTG/exFAT mounts from Android 17 vold)
- SELinux permissive; `KALLSYMS(_ALL)=y`

## System changes

**Framework**
- `framework-res.apk` string defaults patched (tools/fixres.py) — overlays in /system are not applied
  for these framework configs on this port, so set them directly:
  - `config_servicesExtensionPackage` → `com.google.android.ext.services`
  - `config_defaultModuleMetadataProvider` → `com.google.android.modulemetadata`
- `app/com.google.android.modulemetadata` + `ModuleMetadataGoogleOverlay` added
- build.prop additions:
  ```
  dalvik.vm.dex2oat64.enabled=true
  persist.sys.disable_rescue=true
  ro.setupwizard.mode=DISABLED
  persist.sys.setupwizard=FINISH
  wlan.wfd.hdcp=disable
  ```
- `etc/init/zz-bootlog.rc`: one-shot `setupdone` service (provisioned flags, `hidden_api_policy=1`,
  installs `/system/etc/preinst/*.apk` once)
- `etc/init/media.codeclist.generator.rc`: add `seclabel u:r:mediaserver:s0`
  (otherwise mediaserver hangs → storage/SMS hang)
- init.rc: `trigger load-bpf-programs` enabled

**APEX**
- `com.google.android.tethering` (capex): netbpfload kernel-version checks (4) → `b`,
  resolver/clat abort nops, service-connectivity dex patches (ringbuf listener disabled — no BPF ringbuf on 4.14).
  Re-signed with own key, original salt; outer `apex_manifest.pb` root digest updated; APK Sig Block kept.
- `com.android.runtime`: merged A17 64-bit + A16 32-bit (linker, bionic, crash_dump32) for 32-bit HALs;
  signing block restored.
- `com.android.bt`: `libbluetooth_jni.so` @0x7aa8d0 `cbz x0` → `b 0x7aa8c4` (skip VaultKeeper read loop, fixes BLE_START_TIMEOUT)
- After changing a capex: clear `/data/apex/decompressed`.

**Libraries**
- `/system/lib` from A16 (761 files) for 32-bit support; `bin/linker` → runtime APEX linker
- `lib64/libstagefright.so` @0xf3118: `mov w2,#0x200` → `mov w2,#0xff`
  (Samsung `ACodec::reconfigEncoder4OtherApps` freads 512 bytes into a 255-byte buffer → FORTIFY abort in remotedisplay)

**Apps**
- Removed: SecSetupWizard, SetupWizard, SamsungDeviceHealthManagerService
- Restored (debloat went too far → "Device locked" screen): telephony/Knox apps incl. CIDManager,
  CarrierDefaultApp, SimAppDialog, KnoxCore …
- Restored `app/AllshareMediaShare` (Nearby Service — needed by Smart View)
- GmsCore.apk taken from the 8.5 (A16) product - the S26 FE product only ships the AndroidPlatformServices sub-module, so clean installs bootlooped without it (fixed in v1.1)
- Added from S26 FE product: Chrome64, TrichromeLibrary64, WebViewGoogle64, Phonesky, GmsCore,
  product-* permission/sysconfig xmls (NOT `product-google-staged-installer-whitelist.xml` → "Multiple modules installers")

## Vendor changes
- audio HAL, camera provider, OMX rc files re-enabled; audio HAL entries restored in vintf manifest
- Camera stack rebuilt from stock Samsung firmware: A50 (A505G) HAL, libexynoscamera3, libFacePreProcessing, sensor setfiles + fimc firmware; A51 (A515FXXU8HWI1) Android 13 camera framework, provider and unihal apex (fixes empty JPEG / Exif 0x0 thumb)

## Smart View — where it stops
1. Nearby Service missing → restore AllshareMediaShare ✔
2. HDCP trustlet refused by TEE (unlocked bootloader) → `wlan.wfd.hdcp=disable` ✔
3. remotedisplay FORTIFY abort → libstagefright patch ✔
4. **Black screen**: `MediaCodec: buffer offset and size goes beyond the capacity: size=24, cap=12` —
   64-bit WFD sends 64-bit `VideoNativeMetadata` to the A50's **32-bit-only** OMX service
   (`OMX.Exynos.AVC.Encoder`). WFD only accepts hardware encoders. Needs a 64-bit
   `android.hardware.media.omx@1.0-service` (and 64-bit libstagefright_omx) — open.

## Build
See `build.sh`. EROFS images via SuperR's `mkfs.erofs` with fs_config / file_contexts.
New files need fs_config + file_contexts entries (`tools/addcfg.py <subdir>`); blank lines break mkfs.

## Tools
- `tools/fixres.py` — set string resources in framework-res.apk (keeps signing block)
- `tools/addcfg.py` — add fs_config / file_contexts entries for new paths
- `tools/why.sh` — summarize a boot log (zygote / system_server / native crashes)
- `tools/sv.sh` — Smart View / WFD log filter

## Lessons
- Don't flash an old ROM's product partition under a new system: its A16 flags/props broke zygote (`SystemServiceRegistry` NoClassDefFoundError).
- Changing `ro.vendor.build.fingerprint` triggers an "upgrade" boot path — caused watchdog/boot hangs; leave it. The "internal problem" dialog is harmless.
- Keep a known-good image set before every experiment.

## Changelog
- v1.4: Samsung Camera, dual speaker, Gallery fix
- v1.3: install options menu (volume keys), swipe gestures fixed, Samsung Clock added
- v1.2: Smart View, fingerprint, Play Services/WebView fix, odsign/ART fix, f2fs + ext4 data, Messages/Galaxy Store/Wallpapers, Shelter
- v1.1: GmsCore fix
See PATCHES.md for details.
