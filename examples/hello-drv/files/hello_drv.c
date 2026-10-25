/* SPDX-License-Identifier: GPL-2.0-only */
#include <linux/init.h>
#include <linux/module.h>
#include <linux/printk.h>

static int __init hello_drv_init(void)
{
  pr_info("hello_drv: loaded\n");
  return 0;
}

static void __exit hello_drv_exit(void)
{
  pr_info("hello_drv: unloaded\n");
}

module_init(hello_drv_init);
module_exit(hello_drv_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Yocto kernel module test");
