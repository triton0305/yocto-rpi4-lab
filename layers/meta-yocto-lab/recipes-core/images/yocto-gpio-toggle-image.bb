require recipes-core/images/core-image-minimal.bb
SUMMARY = "Raspberry Pi 4 UART and original eight-channel GPIO toggle image"
COMPATIBLE_MACHINE = "^raspberrypi4-64$"
# module.bbclass makes lab-gpio depend on the actual ABI-suffixed module package.
IMAGE_INSTALL:append = " lab-gpio lab-gpio-test lab-gpio-autostart shadow"
IMAGE_FEATURES:remove = "debug-tweaks allow-empty-password empty-root-password"
EXTRA_IMAGE_FEATURES:remove = "debug-tweaks allow-empty-password empty-root-password"
IMAGE_FEATURES:append = " allow-root-login"
IMAGE_FSTYPES = "wic.bz2 wic.bmap"

# shadow supplies SHA-512-capable login/passwd and creates /etc/shadow.
# Read only a private local hash at task execution; never expand it into metadata
# or generated task scripts. Generate with scripts/prepare-gpio-credentials.py.
GPIO_PASSWORD_FILE ?= "${TOPDIR}/conf/gpio-private/root-password.hash"
do_rootfs[file-checksums] += "${GPIO_PASSWORD_FILE}:True"
ROOTFS_POSTPROCESS_COMMAND:append = " gpio_set_root_password;"
python gpio_set_root_password() {
    import pathlib, re
    secret = pathlib.Path(d.getVar('GPIO_PASSWORD_FILE'))
    if not secret.is_file() or secret.stat().st_mode & 0o077:
        bb.fatal('Create private mode-0600 GPIO_PASSWORD_FILE before building this image')
    value = secret.read_text().strip()
    if not re.fullmatch(r'\$6\$[./A-Za-z0-9]{1,16}\$[./A-Za-z0-9]{86}', value):
        bb.fatal('GPIO_PASSWORD_FILE must contain a SHA-512 crypt password hash')
    shadow = pathlib.Path(d.getVar('IMAGE_ROOTFS')) / 'etc/shadow'
    lines = shadow.read_text().splitlines()
    roots = 0
    for i, line in enumerate(lines):
        fields = line.split(':')
        if fields[0] == 'root':
            fields[1] = value
            lines[i] = ':'.join(fields)
            roots += 1
    if roots != 1:
        bb.fatal('Expected exactly one root shadow entry')
    shadow.write_text('\n'.join(lines) + '\n')
}

# Preserve shared BSP deployment. Only this image consumes the private copy.
IMAGE_BOOT_FILES:remove = "${BOOTFILES_DIR_NAME}/*"
IMAGE_BOOT_FILES:append = " gpio-toggle-boot/* devicetree/lab-gpio-eight-overlay.dtbo;overlays/lab-gpio-eight-overlay.dtbo"
do_prepare_gpio_boot[depends] += "rpi-bootfiles:do_deploy lab-gpio-overlay:do_deploy"
python do_prepare_gpio_boot() {
    import pathlib, shutil, re
    if d.getVar('RPI_USE_U_BOOT') == '1':
        bb.fatal('This integration requires direct firmware boot; U-Boot is not validated')
    deploy = pathlib.Path(d.getVar('DEPLOY_DIR_IMAGE'))
    dest = deploy / 'gpio-toggle-boot'
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(deploy / d.getVar('BOOTFILES_DIR_NAME'), dest)
    config = dest / 'config.txt'
    original = config.read_text()
    if re.search(r'^\s*(?:include\s|dtoverlay\s*=\s*lab-gpio)', original, re.M):
        bb.fatal('Review pre-existing config includes or lab-gpio overlays before integration')
    config.write_text(original + '\n# Final GPIO image only\n[all]\nenable_uart=1\ndtoverlay=lab-gpio-eight-overlay\n')
    cmdline = dest / 'cmdline.txt'
    args = cmdline.read_text().split()
    # Preserve root and all non-console arguments; normalize serial aliases.
    args = [a for a in args if not re.match(r'console=(serial[0-9]|ttyAMA[0-9]|ttyS[0-9]),', a)]
    args.append('console=serial0,115200')
    cmdline.write_text(' '.join(args) + '\n')
}
addtask prepare_gpio_boot before do_image_wic after do_rootfs
do_image_wic[depends] += "lab-gpio-overlay:do_deploy"
