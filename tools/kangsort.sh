#!/bin/bash
h(){ find "$1" -type f -size +0 -exec md5sum {} + 2>/dev/null | cut -c1-32 | sort -u; }
h ~/SuperRs-Kitchen_Linux-64_v3.2.2.2/superr_android17 > /tmp/s26.h
h ~/SuperRs-Kitchen_Linux-64_v3.2.2.2/superr_a50_m12 > /tmp/m12.h
: > ~/kang_only_fresh.txt; a=0; b=0; c=0
while read f; do m=$(md5sum < ~/"$f" | cut -c1-32)
  if grep -qx $m /tmp/s26.h; then a=$((a+1)); elif grep -qx $m /tmp/m12.h; then b=$((b+1)); else c=$((c+1)); echo "$f" >> ~/kang_only_fresh.txt; fi
done < ~/kangcheck.txt
echo "stock S26 FE: $a   your M12 port: $b   NOT in either: $c"; head -30 ~/kang_only_fresh.txt
