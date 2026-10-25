obj-m := hello_drv.o

all:
	$(MAKE) -C $(KERNEL_SRC) O=$(O) M=$(CURDIR) modules

modules_install:
	$(MAKE) -C $(KERNEL_SRC) O=$(O) M=$(CURDIR) modules_install
