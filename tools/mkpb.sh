set -e
D=~/urpb; rm -rf $D; mkdir -p $D/res/values
cat > $D/AndroidManifest.xml <<'X'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.ultimaterom.protectedbroadcasts">
    <protected-broadcast android:name="com.sec.android.app.setupwizard.SETUPWIZARD_COMPLETE"/>
    <protected-broadcast android:name="com.sec.android.app.secsetupwizard.SETUPWIZARD_COMPLETE"/>
    <protected-broadcast android:name="com.samsung.accessibility.ACCESSIBILITY_HOME_APPLIANCE_BACKUP"/>
    <application android:hasCode="false" android:label="@string/app_name"/>
</manifest>
X
printf '<?xml version="1.0" encoding="utf-8"?>\n<resources><string name="app_name">UR Protected Broadcasts</string></resources>\n' > $D/res/values/strings.xml
printf "version: 2.9.3\napkFileName: URProtectedBroadcasts.apk\nisFrameworkApk: false\nusesFramework:\n  ids:\n  - 1\nsdkInfo:\n  minSdkVersion: '30'\n  targetSdkVersion: '30'\npackageInfo:\n  forcedPackageId: '127'\nversionInfo:\n  versionCode: '1'\n  versionName: '1.0'\ndoNotCompress:\n- resources.arsc\n" > $D/apktool.yml
cd ~ && java -jar ~/softap/apktool.jar b -o /tmp/pb_u.apk $D | tail -1
zipalign -f -p 4 /tmp/pb_u.apk /tmp/pb_a.apk
apksigner sign --ks ~/ur_rom.jks --ks-pass pass:urrompass --out /tmp/pb.apk /tmp/pb_a.apk
S=~/s26fe/sys17; A=system/system/app/URProtectedBroadcasts
mkdir -p $S/$A && cp /tmp/pb.apk $S/$A/URProtectedBroadcasts.apk
grep -q "$A " $S/config/system_fs_config || printf "$A 0 0 0755\n$A/URProtectedBroadcasts.apk 0 0 0644\n" >> $S/config/system_fs_config
grep -q "URProtectedBroadcasts\\\\.apk" $S/config/system_file_contexts || printf "/$A u:object_r:system_file:s0\n/$A/URProtectedBroadcasts\\\\.apk u:object_r:system_file:s0\n" >> $S/config/system_file_contexts
aapt dump xmltree $S/$A/URProtectedBroadcasts.apk AndroidManifest.xml | grep -c protected-broadcast
