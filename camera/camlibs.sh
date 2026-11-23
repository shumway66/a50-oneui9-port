cd ~/m12x; S=~/s26fe/sys17/system/system; B=~/cmp/camlibs_s26; rm -rf libs; mkdir -p libs $B
dbg(){ debugfs -R "$1" system.img 2>/dev/null; }
Q=""; for t in public.libraries-arcsoft.txt public.libraries-camera.samsung.txt public.libraries-polarr.txt; do
  dbg "cat /system/etc/$t" > libs_$t; Q="$Q $(grep -v '^#' libs_$t | awk '{print $1}')"; done
done_list=" "
while [ -n "$(echo $Q)" ]; do
  set -- $Q; l=$1; shift; Q="$*"
  case "$done_list" in *" $l "*) continue;; esac; done_list="$done_list$l "
  dbg "dump /system/lib64/$l libs/$l"; [ -s libs/$l ] || { rm -f libs/$l; continue; }
  for n in $(readelf -d libs/$l 2>/dev/null | sed -n 's/.*NEEDED.*\[\(.*\)\]/\1/p'); do
    [ -e $S/lib64/$n ] || [ -e /dev/null -a -n "$(ls $S/../../system/apex 2>/dev/null | head -0)" ] ; [ -e $S/lib64/$n ] || Q="$Q $n"; done
done
n=0; for f in libs/*.so; do b=$(basename $f); [ -e $S/lib64/$b ] && cp -n $S/lib64/$b $B/; cp $f $S/lib64/$b; n=$((n+1)); done
for t in public.libraries-arcsoft.txt public.libraries-camera.samsung.txt public.libraries-polarr.txt; do
  touch $S/etc/$t; cat $S/etc/$t libs_$t | grep -v '^\s*$' | sort -u > /tmp/u && cp /tmp/u $S/etc/$t; done
echo "copied $n libs (S26 originals backed up: $(ls $B | wc -l))"
for f in libs/*.so; do for d in $(readelf -d $f | sed -n 's/.*NEEDED.*\[\(.*\)\]/\1/p'); do [ -e $S/lib64/$d ] || echo "still missing: $d (for $(basename $f))"; done; done | sort -u | head -15
