#----- save install options for first boot -----#
is_mounted /cache || mount /cache 2>/dev/null
mkdir -p /cache && cp -f /tmp/ur_choices /cache/ur_choices && chmod 0644 /cache/ur_choices
rm -f /data/local/tmp/.ur_setup_done 2>/dev/null
ui_print "   - Install options saved"
#------------------------------------------------#
