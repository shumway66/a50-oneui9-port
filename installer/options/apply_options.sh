#!/bin/bash
# Adds optional apps + first-boot script to the system tree. Run on the laptop.
set -e
K=~/SuperRs-Kitchen_Linux-64_v3.2.2.2/superr_android17; S=~/s26fe/sys17/system/system
# 1) optional system apps (keep app/priv-app status)
for n in Gmail2 Maps YouTube Photos GoogleCalendarSyncAdapter Bixby BixbyWakeup BixbyInterpreter Routines SamsungWeather SamsungTTSVoice_en_US_l03 SamsungTTSVoice_en_GB_f00; do
  src=$(cd $K; ls -d system/system/app/$n system/system/priv-app/$n product/app/$n product/priv-app/$n system_ext/app/$n system_ext/priv-app/$n 2>/dev/null | head -1)
  [ -z "$src" ] && { echo "!! $n not found"; continue; }
  case "$src" in *priv-app*) dst=priv-app;; *) dst=app;; esac
  [ -e $S/$dst/$n ] || cp -a $K/$src $S/$dst/
  echo "added $n -> $dst"; python3 ~/addcfg.py $dst/$n >/dev/null
done
# 2) their permission/sysconfig files if missing
for x in $(grep -rlaiE 'bixby|routines|daemonapp|SMT|\.apps\.maps|\.gm"|youtube|apps\.photos|syncadapters\.calendar' $K/system/system/etc/permissions $K/product/etc/permissions $K/system/system/etc/sysconfig $K/product/etc/sysconfig $K/system/system/etc/default-permissions $K/product/etc/default-permissions 2>/dev/null); do
  sub=$(basename $(dirname $x)); b=$(basename $x)
  [ -e $S/etc/$sub/$b ] || { mkdir -p $S/etc/$sub; cp $x $S/etc/$sub/; echo "perm $sub/$b"; }
done
python3 ~/addcfg.py etc >/dev/null
# 3) preinstall folders: Clock always; extras optional
mkdir -p $S/etc/preinst_opt
cp ~/extra_apks/SamsungClock.apk $S/etc/preinst/
for a in OpenCamera APatch Shelter; do [ -f $S/etc/preinst/$a.apk ] && mv $S/etc/preinst/$a.apk $S/etc/preinst_opt/; done
rm -f $S/etc/preinst/LibreCamera.apk
cp ~/ur_firstboot.sh $S/etc/ur_firstboot.sh
python3 ~/addcfg.py etc >/dev/null
sed -i '/^\s*$/d' ~/s26fe/sys17/config/system_fs_config ~/s26fe/sys17/config/system_file_contexts
echo "preinst: $(ls $S/etc/preinst | tr '\n' ' ')"; echo "preinst_opt: $(ls $S/etc/preinst_opt | tr '\n' ' ')"
# 4) point the first-boot service at the script
cat > $S/etc/init/zz-bootlog.rc <<'R'
on property:sys.boot_completed=1
    start setupdone

service setupdone /system/bin/sh /system/etc/ur_firstboot.sh
    user root
    group root system
    seclabel u:r:shell:s0
    disabled
    oneshot
R
echo "init rc updated"
