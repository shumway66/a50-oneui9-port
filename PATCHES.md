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
