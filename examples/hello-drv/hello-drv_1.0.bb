SUMMARY = "Hello kernel module for Raspberry Pi 4"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://hello_drv.c;beginline=1;endline=1;md5=a9f1449b768f69dcffc44cb5e556b102"

SRC_URI = "file://hello_drv.c file://Makefile"
S = "${UNPACKDIR}"

inherit module
