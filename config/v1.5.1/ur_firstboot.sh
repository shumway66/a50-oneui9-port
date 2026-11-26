#!/system/bin/sh
# Ultimate Rom first-boot setup: provisioning flags + installer choices (runs once)
settings put global device_provisioned 1
settings put secure user_setup_complete 1
settings put global hidden_api_policy 1
M=/data/local/tmp/.ur_setup_done
[ -f $M ] && exit 0
L=/data/local/tmp/ur_firstboot.log
C=/data/ur_choices; [ -f $C ] || C=/cache/ur_choices; [ -f $C ] && . $C
pm grant com.google.android.gms android.permission.ACCESS_LOCAL_NETWORK 2>/dev/null; pm grant com.google.android.gms android.permission.NEARBY_WIFI_DEVICES 2>/dev/null
echo "choices: google=$google bixby=$bixby weather=$weather voice=$voice opencam=$opencam shelter=$shelter apatch=$apatch" > $L
rm_dir() {
  for d in "$@"; do
    for p in $(pm list packages -f | grep -F "/$d/" | sed 's/.*=//'); do
      echo "remove $d ($p): $(pm uninstall --user 0 $p 2>&1)" >> $L
    done
  done
}
[ "$google" = 0 ]  && rm_dir Gmail2 Maps YouTube Photos GoogleCalendarSyncAdapter
[ "$bixby" = 0 ]   && rm_dir Bixby BixbyWakeup BixbyInterpreter Routines
[ "$weather" = 0 ] && rm_dir SamsungWeather
[ "$voice" = 0 ]   && rm_dir SamsungTTSVoice_en_US_l03 SamsungTTSVoice_en_GB_f00
for a in /system/etc/preinst/*.apk; do echo "install $a: $(pm install -r $a 2>&1)" >> $L; done
O=/system/etc/preinst_opt
[ "$opencam" != 0 ] && echo "install OpenCamera: $(pm install -r $O/OpenCamera.apk 2>&1)" >> $L
[ "$shelter" != 0 ] && echo "install Shelter: $(pm install -r $O/Shelter.apk 2>&1)" >> $L
[ "$apatch" != 0 ]  && echo "install APatch: $(pm install -r $O/APatch.apk 2>&1)" >> $L
touch $M
