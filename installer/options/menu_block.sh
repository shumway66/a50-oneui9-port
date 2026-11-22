#----- Ultimate Rom install options (volume keys) -----#
ur_key() {
    if ! command -v getevent >/dev/null 2>&1; then return 0; fi
    while true; do
        ev=$(getevent -lqc 1 2>/dev/null)
        case "$ev" in
            *KEY_VOLUMEUP*DOWN*) return 0 ;;
            *KEY_VOLUMEDOWN*DOWN*) return 1 ;;
        esac
    done
}
ur_ask() {
    ui_print " "
    ui_print "  $1"
    ui_print "     Vol+ = YES     Vol- = NO"
    if ur_key; then ui_print "     -> Yes"; echo "$2=1" >> /tmp/ur_choices; else ui_print "     -> No"; echo "$2=0" >> /tmp/ur_choices; fi
}
rm -f /tmp/ur_choices
ui_print "==============================================="
ui_print "  INSTALL OPTIONS  (answer with volume keys)"
ui_print "==============================================="
ur_ask "Google apps? (Gmail, Maps, YouTube, Photos)" google
ur_ask "Bixby + Modes & Routines?" bixby
ur_ask "Samsung Weather?" weather
ur_ask "Samsung English voices (text-to-speech)?" voice
ur_ask "Open Camera?" opencam
ur_ask "Shelter (clone any app)?" shelter
ur_ask "APatch (root manager)?" apatch
ui_print " "
#-------------------------------------------------------#
