# Port patches (v1.2 - v1.3)

## framework-res (tools/fixres.py, tools/fixaxml.py)
- config_servicesExtensionPackage = com.google.android.ext.services
- config_defaultModuleMetadataProvider = com.google.android.modulemetadata
- config_webview_packages: com.android.webview -> com.google.android.webview (fixes Play Services crash / sign-in)

## framework.jar (tools/dexret.py)
- android.os.Build.isBuildConsistent -> always true (removes "internal problem" popup)

## ART / odsign (config/odsign.rc)
- Samsung TEE refuses odsign keys on 4.14, so odsign.rc runs odrefresh --compile and sets the odsign props itself
- Prebuilt framework/arm64 + framework/oat removed (CMC GC boot image needs userfaultfd)

## Smart View (system/lib64/libstagefright.so)
- 0xf3118: 02408052 -> e21f8052 (fread FORTIFY fix)
- 0xdc11c: 97018052 -> 17038052 (DynamicANWBuffer size 12 -> 24)
- 0xcc7a0: 28-instruction code cave in ACodec::BaseState::onInputBufferFilled (64-bit VideoNativeMetadata -> GraphicBuffer -> emptyBuffer)
- build.prop: wlan.wfd.hdcp=disable

## Fingerprint (floating_feature.xml)
- Removed SEC_FLOATING_FEATURE_LCD_CONFIG_LOCAL_HBM and LCD_SUPPORT_SELFMASK (A50 uses mask_brightness)

## Overlays
- /system/overlay is NOT scanned on this port. Overlays must go in /system/system_ext/overlay (or /vendor/overlay).
- Navbar overlays moved there -> swipe gestures work

## Install options (installer/options)
- Volume-key menu in updater-script, choices saved to /cache and /data (after cleanup.sh, which wipes /cache)
- ur_firstboot.sh applies them on first boot (pm uninstall --user 0 / pm install)

## Samsung Camera (v1.4) - camera/
- App: SamsungCamera from the A50 M12 port (One UI 5.1), cameradata from the same ROM
- campatch.py patches the app:
  - ro.build.version.oneui 90000 unknown -> fall back to newest known version (m3/i)
  - semSetDisablePreviewScreenshots removed in One UI 9 -> nop
  - getCurrentUser needs platform-only permission -> returns 0
  - APK re-signed with a ROM key (v2 signature required); key kept private
- floating_feature: S26 FE camera keys replaced with the M12 port's (CAMID_WIDE=0, CAMID_UW=50)
- camlibs.sh: copies the M12 camera / arcsoft / polarr libs + public.libraries entries
- camshim.S: libcamshim.camera.samsung.so maps the old
  CameraUtils::getRotationTransform(meta,int,int*) to the A17 (meta,int,bool,int*) version;
  added as NEEDED to libcore2nativeutil.camera.samsung.so with patchelf
- apicheck.py: lists framework calls an app makes that the ROM's framework lacks

## Gallery (v1.4)
- libphotohdr.so uses ARMv8.2 instructions (SIGILL on Exynos 9610)
- floating_feature: MMFW_SUPPORT_PHOTOHDR and COMMON_SUPPORT_HDR_EFFECT = FALSE

## Dual speaker (v1.4)
- vendor/etc/mixer_paths.xml: <path name="dev-handset" /> added to media-speaker

## v1.5.1 fixes

### Framework (system/framework/framework.jar) - tools/patch_arsc2.py
- Android's "resources.arsc must be uncompressed and 4-byte aligned" check misfires on this port for every APK (even correctly aligned stock ones). After the package cache is cleared it rejects core APEX modules and the phone loops to recovery ("recoveryDecompressedApex"). It also blocked Smart Capture and Galaxy Store updates.
- Fix: patch_arsc2.py replaces the single call to AssetManager.containsAllocatedTable() in the package parser with "false" (const/16 + nops), leaving AssetManager itself untouched (patching the method breaks ART verification).

### SELinux labels (config/system_file_contexts)
- /system/bin/zygote_next -> zygote_next_exec, /system/bin/charger -> charger_exec, /system/bin/mmd -> mmd_exec (were system_file; init refused to start them).

### Screenshots / debug level
- ro.debug_level 0x494d (MID) -> 0x4f4c (LOW) in system and vendor build.prop. MID started a full dumpstate on every screenshot key combo.

### Samsung Camera video (cameradata/camera-feature.xml)
- Video snapshot sizes the A50 HAL doesn't offer replaced: 4032x2268 -> 3840x2160, 4032x1860 -> 3296x1520, 4032x3024 -> 4688x3516.
- Video HDR, VDIS and Super-VDIS set false for all camcorder sizes (EIS stalls the sensor pipeline; camera HAL gets no gyro data yet).

### Always On Display (vendor overlay framework-res__auto_generated_rro_vendor.apk)
- Added config_dozeAlwaysOnDisplayAvailable=true and config_aodBrightnessValues (0,40,71,94 from the A50 vendor). Without the array the AOD plugin crashes ("getBrightnessValues must not be null").

### Smart Capture (screenshot toolbar)
- Restored system/app/SmartCapture from stock S26 FE (SM-S741B, Android 17) plus its default-permissions file.

### Accessibility settings crash - tools/mkpb.sh
- AccessibilityManagerService failed to start: its receiver listens for Samsung setup-wizard broadcasts that were declared protected only by the debloated SecSetupWizard.
- Fix: small system app "UR Protected Broadcasts" (com.ultimaterom.protectedbroadcasts) declaring the 3 broadcasts protected, added to allowed-system-preload-apps.xml.

### "Choose a device to connect" pop-up (Cast)
- default-permissions-ur-gms.xml grants ACCESS_LOCAL_NETWORK + NEARBY_WIFI_DEVICES to Google Play services; ur_firstboot.sh grants them on dirty flashes.

### Bluetooth audio (build.prop)
- persist.bluetooth.a2dp_offload.disabled=true, ro.bluetooth.a2dp_offload.supported=false.

### Kernel v3.0 (4.14.357 OpenELA) - see kernel repo tag v3.0
- sensorhub: sensor_spec converted from 44-byte to 46-byte records for the One UI 5 sensor HAL (auto-rotate, all sensors).
- bpf: LPM-trie delete backported from 4.15 (system_server restart loop).
- capability: CAP_PERFMON/CAP_BPF/CAP_CHECKPOINT_RESTORE defined (Android 17 native zygote walks capabilities to 40 - Chrome/WebView).
- scsc: advertise 5G=no for SoftAP. zram: LZ4K/LZ4KD added. zsmalloc: g_pool cleared on pool destroy (panic after zram reset).

### Provenance check - tools/kangcheck.sh, tools/kangsort.sh
- Hash comparison of the ROM against another ROM's files, sorted into "matches stock S26 FE", "matches own M12 port" and "neither". Used to remove one stray file (camera-frsh.xml) before v1.5.1.

### Known limits
- Galaxy AI / Samsung Language Core: needs libenn_user_lib.so (Exynos NPU); A50 has no NPU.
