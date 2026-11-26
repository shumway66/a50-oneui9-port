#!/bin/bash
# Lists files in Ultimate Rom that are byte-identical to files in Fresh's system/vendor
h(){ find "$1" -type f -size +0 -exec md5sum {} + 2>/dev/null | sort; }
h ~/frshsys > /tmp/f.md5; h ~/frshvnd >> /tmp/f.md5
h ~/s26fe/sys17/system > /tmp/u.md5; h ~/cmp/v17 >> /tmp/u.md5
cut -c1-32 /tmp/f.md5 | sort -u > /tmp/f.h
grep -F -f /tmp/f.h /tmp/u.md5 | awk '{print $2}' | sed "s#$HOME/##" > ~/kangcheck.txt
echo "identical files: $(wc -l < ~/kangcheck.txt)"; grep -i -E "camera|cam|arcsoft|polarr" ~/kangcheck.txt | head -20
