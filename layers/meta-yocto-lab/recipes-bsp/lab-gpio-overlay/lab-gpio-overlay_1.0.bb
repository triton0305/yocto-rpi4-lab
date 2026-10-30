SUMMARY = "Active eight-channel GPIO overlay for the final image"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/GPL-2.0-only;md5=801f80980d171dd6425610833a22dbe6"
SRC_URI = "file://lab-gpio-eight-overlay.dts"
inherit devicetree
COMPATIBLE_MACHINE = "^raspberrypi4-64$"
DT_FILES = "lab-gpio-eight-overlay.dts"
