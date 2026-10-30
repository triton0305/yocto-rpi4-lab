SUMMARY = "SysV lifecycle for the original eight-channel GPIO controller"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"
SRC_URI = "file://lab-gpio-init"
S = "${UNPACKDIR}"
inherit update-rc.d
INITSCRIPT_NAME = "lab-gpio"
INITSCRIPT_PARAMS = "start 99 2 3 4 5 . stop 01 0 1 6 ."
RDEPENDS:${PN} = "lab-gpio-test kmod busybox"
do_install() {
    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${S}/lab-gpio-init ${D}${sysconfdir}/init.d/lab-gpio
}
