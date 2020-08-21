/* Copyright (c) 2017 Arista Networks, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/sysfs.h>
#include <linux/version.h>
#include <linux/hwmon.h>
#include <linux/hwmon-sysfs.h>
#include <linux/gpio.h>
#include <linux/stat.h>

#include "scd.h"
#include "scd-attrs.h"
#include "scd-fan.h"
#include "scd-hwmon.h"
#include "scd-led.h"
#include "scd-mdio.h"
#include "scd-smbus.h"

#define SCD_MODULE_NAME "scd-hwmon"

#define RESET_SET_OFFSET 0x00
#define RESET_CLEAR_OFFSET 0x10

#define MAX_CONFIG_LINE_SIZE 100

struct scd_gpio_attribute {
   struct device_attribute dev_attr;
   struct scd_context *ctx;

   u32 addr;
   u32 bit;
   u32 active_low;
};

#define GPIO_NAME_MAX_SZ 32
struct scd_xcvr_attribute {
   struct device_attribute dev_attr;
   struct scd_xcvr *xcvr;

   char name[GPIO_NAME_MAX_SZ];
   u32 bit;
   u32 active_low;
   u32 clear_on_read;
   u32 clear_on_read_value;
};

struct scd_gpio {
   char name[GPIO_NAME_MAX_SZ];
   struct scd_gpio_attribute attr;
   struct list_head list;
};

#define XCVR_ATTR_MAX_COUNT 9
struct scd_xcvr {
   struct scd_context *ctx;
   struct scd_xcvr_attribute attr[XCVR_ATTR_MAX_COUNT];
   struct list_head list;

   char name[GPIO_NAME_MAX_SZ];
   u32 addr;
};

#define to_scd_gpio_attr(_dev_attr) \
   container_of(_dev_attr, struct scd_gpio_attribute, dev_attr)

#define to_scd_xcvr_attr(_dev_attr) \
   container_of(_dev_attr, struct scd_xcvr_attribute, dev_attr)

#define SCD_GPIO_ATTR(_name, _mode, _show, _store, _ctx, _addr, _bit, _active_low) \
   { .dev_attr = __ATTR_NAME_PTR(_name, _mode, _show, _store),                     \
     .ctx = _ctx,                                                                  \
     .addr = _addr,                                                                \
     .bit = _bit,                                                                  \
     .active_low = _active_low                                                     \
   }

#define SCD_RW_GPIO_ATTR(_name, _ctx, _addr, _bit, _active_low)                    \
   SCD_GPIO_ATTR(_name, S_IRUGO | S_IWUSR, attribute_gpio_get, attribute_gpio_set, \
                 _ctx, _addr, _bit, _active_low)

#define SCD_RO_GPIO_ATTR(_name, _ctx, _addr, _bit, _active_low) \
   SCD_GPIO_ATTR(_name, S_IRUGO, attribute_gpio_get, NULL,      \
                 _ctx, _addr, _bit, _active_low)

#define SCD_XCVR_ATTR(_xcvr_attr, _name, _name_size, _mode, _show, _store, _xcvr, \
                      _bit, _active_low, _clear_on_read)                          \
   do {                                                                           \
      snprintf(_xcvr_attr.name, _name_size, _name);                               \
      _xcvr_attr.dev_attr =                                                       \
         (struct device_attribute)__ATTR_NAME_PTR(_xcvr_attr.name, _mode, _show,  \
                                                  _store);                        \
      _xcvr_attr.xcvr = _xcvr;                                                    \
      _xcvr_attr.bit = _bit;                                                      \
      _xcvr_attr.active_low = _active_low;                                        \
      _xcvr_attr.clear_on_read = _clear_on_read;                                  \
   } while(0);

#define SCD_RW_XCVR_ATTR(_xcvr_attr, _name, _name_size, _xcvr, _bit,  \
                         _active_low, _clear_on_read)                 \
   SCD_XCVR_ATTR(_xcvr_attr, _name, _name_size, S_IRUGO | S_IWUSR,    \
                 attribute_xcvr_get, attribute_xcvr_set, _xcvr, _bit, \
                 _active_low, _clear_on_read)

#define SCD_RO_XCVR_ATTR(_xcvr_attr, _name, _name_size, _xcvr, _bit,         \
                         _active_low, _clear_on_read)                        \
   SCD_XCVR_ATTR(_xcvr_attr, _name, _name_size, S_IRUGO, attribute_xcvr_get, \
                 NULL, _xcvr, _bit, _active_low, _clear_on_read)

struct scd_reset_attribute {
   struct device_attribute dev_attr;
   struct scd_context *ctx;

   u32 addr;
   u32 bit;
};

#define RESET_NAME_MAX_SZ 50
struct scd_reset {
   char name[RESET_NAME_MAX_SZ];
   struct scd_reset_attribute attr;
   struct list_head list;
};

#define to_scd_reset_attr(_dev_attr) \
   container_of(_dev_attr, struct scd_reset_attribute, dev_attr)

#define SCD_RESET_ATTR(_name, _ctx, _addr, _bit)                                \
   { .dev_attr = __ATTR_NAME_PTR(_name, S_IRUGO | S_IWUSR, attribute_reset_get, \
                                 attribute_reset_set),                          \
     .ctx = _ctx,                                                               \
     .addr = _addr,                                                             \
     .bit = _bit,                                                               \
   }

/* locking functions */
static struct mutex scd_hwmon_mutex;

static void module_lock(void)
{
   mutex_lock(&scd_hwmon_mutex);
}

static void module_unlock(void)
{
   mutex_unlock(&scd_hwmon_mutex);
}

static void scd_lock(struct scd_context *ctx)
{
   mutex_lock(&ctx->mutex);
}

static void scd_unlock(struct scd_context *ctx)
{
   mutex_unlock(&ctx->mutex);
}

static struct list_head scd_list;

static struct scd_context *get_context_for_pdev(struct pci_dev *pdev)
{
   struct scd_context *ctx;

   module_lock();
   list_for_each_entry(ctx, &scd_list, list) {
      if (ctx->pdev == pdev) {
         module_unlock();
         return ctx;
      }
   }
   module_unlock();

   return NULL;
}

static struct scd_context *get_context_for_dev(struct device *dev)
{
   struct scd_context *ctx;

   module_lock();
   list_for_each_entry(ctx, &scd_list, list) {
      if (get_scd_dev(ctx) == dev) {
         module_unlock();
         return ctx;
      }
   }
   module_unlock();

   return NULL;
}

static ssize_t attribute_gpio_get(struct device *dev,
                                  struct device_attribute *devattr, char *buf)
{
   const struct scd_gpio_attribute *gpio = to_scd_gpio_attr(devattr);
   u32 reg = scd_read_register(gpio->ctx->pdev, gpio->addr);
   u32 res = !!(reg & (1 << gpio->bit));
   res = (gpio->active_low) ? !res : res;
   return sprintf(buf, "%u\n", res);
}

static ssize_t attribute_gpio_set(struct device *dev,
                                  struct device_attribute *devattr,
                                  const char *buf, size_t count)
{
   const struct scd_gpio_attribute *gpio = to_scd_gpio_attr(devattr);
   long value;
   int res;
   u32 reg;

   res = kstrtol(buf, 10, &value);
   if (res < 0)
      return res;

   if (value != 0 && value != 1)
      return -EINVAL;

   reg = scd_read_register(gpio->ctx->pdev, gpio->addr);
   if (gpio->active_low) {
      if (value)
         reg &= ~(1 << gpio->bit);
      else
         reg |= ~(1 << gpio->bit);
   } else {
      if (value)
         reg |= 1 << gpio->bit;
      else
         reg &= ~(1 << gpio->bit);
   }
   scd_write_register(gpio->ctx->pdev, gpio->addr, reg);

   return count;
}

static u32 scd_xcvr_read_register(const struct scd_xcvr_attribute *gpio)
{
   struct scd_xcvr *xcvr = gpio->xcvr;
   int i;
   u32 reg;

   reg = scd_read_register(gpio->xcvr->ctx->pdev, gpio->xcvr->addr);
   for (i = 0; i < XCVR_ATTR_MAX_COUNT; i++) {
      if (xcvr->attr[i].clear_on_read) {
         xcvr->attr[i].clear_on_read_value =
            xcvr->attr[i].clear_on_read_value | !!(reg & (1 << i));
      }
   }
   return reg;
}

static ssize_t attribute_xcvr_get(struct device *dev,
                                  struct device_attribute *devattr, char *buf)
{
   struct scd_xcvr_attribute *gpio = to_scd_xcvr_attr(devattr);
   u32 res;
   u32 reg;

   reg = scd_xcvr_read_register(gpio);
   res = !!(reg & (1 << gpio->bit));
   res = (gpio->active_low) ? !res : res;
   if (gpio->clear_on_read) {
      res = gpio->clear_on_read_value | res;
      gpio->clear_on_read_value = 0;
   }
   return sprintf(buf, "%u\n", res);
}

static ssize_t attribute_xcvr_set(struct device *dev,
                                  struct device_attribute *devattr,
                                  const char *buf, size_t count)
{
   const struct scd_xcvr_attribute *gpio = to_scd_xcvr_attr(devattr);
   long value;
   int res;
   u32 reg;

   res = kstrtol(buf, 10, &value);
   if (res < 0)
      return res;

   if (value != 0 && value != 1)
      return -EINVAL;

   reg = scd_xcvr_read_register(gpio);
   if (gpio->active_low) {
      if (value)
         reg &= ~(1 << gpio->bit);
      else
         reg |= ~(1 << gpio->bit);
   } else {
      if (value)
         reg |= 1 << gpio->bit;
      else
         reg &= ~(1 << gpio->bit);
   }
   scd_write_register(gpio->xcvr->ctx->pdev, gpio->xcvr->addr, reg);

   return count;
}

static void scd_gpio_unregister(struct scd_context *ctx, struct scd_gpio *gpio)
{
   sysfs_remove_file(get_scd_kobj(ctx), &gpio->attr.dev_attr.attr);
}

static void scd_xcvr_unregister(struct scd_context *ctx, struct scd_xcvr *xcvr)
{
   int i;

   for (i = 0; i < XCVR_ATTR_MAX_COUNT; i++) {
      if (xcvr->attr[i].xcvr) {
         sysfs_remove_file(get_scd_kobj(ctx), &xcvr->attr[i].dev_attr.attr);
      }
   }
}

static int scd_gpio_register(struct scd_context *ctx, struct scd_gpio *gpio)
{
   int res;

   res = sysfs_create_file(get_scd_kobj(ctx), &gpio->attr.dev_attr.attr);
   if (res) {
      pr_err("could not create %s attribute for gpio: %d",
             gpio->attr.dev_attr.attr.name, res);
      return res;
   }

   list_add_tail(&gpio->list, &ctx->gpio_list);
   return 0;
}

struct gpio_cfg {
   u32 bitpos;
   bool read_only;
   bool active_low;
   bool clear_on_read;
   const char *name;
};

static int scd_xcvr_register(struct scd_xcvr *xcvr, const struct gpio_cfg *cfgs,
                             size_t gpio_count)
{
   struct gpio_cfg gpio;
   int res;
   size_t i;
   size_t name_size;
   char name[GPIO_NAME_MAX_SZ];

   for (i = 0; i < gpio_count; i++) {
      gpio = cfgs[i];
      name_size = strlen(xcvr->name) + strlen(gpio.name) + 2;
      BUG_ON(name_size > GPIO_NAME_MAX_SZ);
      snprintf(name, name_size, "%s_%s", xcvr->name, gpio.name);
      if (gpio.read_only) {
         SCD_RO_XCVR_ATTR(xcvr->attr[gpio.bitpos], name, name_size, xcvr,
                          gpio.bitpos, gpio.active_low, gpio.clear_on_read);
      } else {
         SCD_RW_XCVR_ATTR(xcvr->attr[gpio.bitpos], name, name_size, xcvr,
                          gpio.bitpos, gpio.active_low, gpio.clear_on_read);
      }
      res = sysfs_create_file(get_scd_kobj(xcvr->ctx),
                              &xcvr->attr[gpio.bitpos].dev_attr.attr);
      if (res) {
         pr_err("could not create %s attribute for xcvr: %d",
                xcvr->attr[gpio.bitpos].dev_attr.attr.name, res);
         return res;
      }
   }

   return 0;
}

/*
 * Must be called with the scd lock held.
 */
static void scd_gpio_remove_all(struct scd_context *ctx)
{
   struct scd_gpio *tmp_gpio;
   struct scd_gpio *gpio;

   list_for_each_entry_safe(gpio, tmp_gpio, &ctx->gpio_list, list) {
      scd_gpio_unregister(ctx, gpio);
      list_del(&gpio->list);
      kfree(gpio);
   }
}

static void scd_xcvr_remove_all(struct scd_context *ctx)
{
   struct scd_xcvr *tmp_xcvr;
   struct scd_xcvr *xcvr;

   list_for_each_entry_safe(xcvr, tmp_xcvr, &ctx->xcvr_list, list) {
      scd_xcvr_unregister(ctx, xcvr);
      list_del(&xcvr->list);
      kfree(xcvr);
   }
}

static ssize_t attribute_reset_get(struct device *dev,
                                   struct device_attribute *devattr, char *buf)
{
   const struct scd_reset_attribute *reset = to_scd_reset_attr(devattr);
   u32 reg = scd_read_register(reset->ctx->pdev, reset->addr);
   u32 res = !!(reg & (1 << reset->bit));
   return sprintf(buf, "%u\n", res);
}

// write 1 -> set, 0 -> clear
static ssize_t attribute_reset_set(struct device *dev,
                                   struct device_attribute *devattr,
                                   const char *buf, size_t count)
{
   const struct scd_reset_attribute *reset = to_scd_reset_attr(devattr);
   u32 offset = RESET_SET_OFFSET;
   long value;
   int res;
   u32 reg;

   res = kstrtol(buf, 10, &value);
   if (res < 0)
      return res;

   if (value != 0 && value != 1)
      return -EINVAL;

   if (!value)
      offset = RESET_CLEAR_OFFSET;

   reg = 1 << reset->bit;
   scd_write_register(reset->ctx->pdev, reset->addr + offset, reg);

   return count;
}

static void scd_reset_unregister(struct scd_context *ctx, struct scd_reset *reset)
{
   sysfs_remove_file(get_scd_kobj(ctx), &reset->attr.dev_attr.attr);
}

static int scd_reset_register(struct scd_context *ctx, struct scd_reset *reset)
{
   int res;

   res = sysfs_create_file(get_scd_kobj(ctx), &reset->attr.dev_attr.attr);
   if (res) {
      pr_err("could not create %s attribute for reset: %d",
             reset->attr.dev_attr.attr.name, res);
      return res;
   }

   list_add_tail(&reset->list, &ctx->reset_list);
   return 0;
}

/*
 * Must be called with the scd lock held.
 */
static void scd_reset_remove_all(struct scd_context *ctx)
{
   struct scd_reset *tmp_reset;
   struct scd_reset *reset;

   list_for_each_entry_safe(reset, tmp_reset, &ctx->reset_list, list) {
      scd_reset_unregister(ctx, reset);
      list_del(&reset->list);
      kfree(reset);
   }
}

static int scd_xcvr_add(struct scd_context *ctx, const char *prefix,
                        const struct gpio_cfg *cfgs, size_t gpio_count,
                        u32 addr, u32 id)
{
   struct scd_xcvr *xcvr;
   int err;

   xcvr = kzalloc(sizeof(*xcvr), GFP_KERNEL);
   if (!xcvr) {
      err = -ENOMEM;
      goto fail;
   }

   err = snprintf(xcvr->name, sizeof_field(typeof(*xcvr), name),
                  "%s%u", prefix, id);
   if (err < 0) {
      goto fail;
   }

   xcvr->addr = addr;
   xcvr->ctx = ctx;

   err = scd_xcvr_register(xcvr, cfgs, gpio_count);
   if (err) {
      goto fail;
   }

   list_add_tail(&xcvr->list, &ctx->xcvr_list);
   return 0;

fail:
   if (xcvr)
      kfree(xcvr);

   return err;
}

static int scd_xcvr_sfp_add(struct scd_context *ctx, u32 addr, u32 id)
{
   static const struct gpio_cfg sfp_gpios[] = {
      {0, true,  false, false, "rxlos"},
      {1, true,  false, false, "txfault"},
      {2, true,  true,  false, "present"},
      {3, true,  false, true,  "rxlos_changed"},
      {4, true,  false, true,  "txfault_changed"},
      {5, true,  false, true,  "present_changed"},
      {6, false, false, false, "txdisable"},
      {7, false, false, false, "rate_select0"},
      {8, false, false, false, "rate_select1"},
   };

   scd_dbg("sfp %u @ 0x%04x\n", id, addr);
   return scd_xcvr_add(ctx, "sfp", sfp_gpios, ARRAY_SIZE(sfp_gpios), addr, id);
}

static int scd_xcvr_qsfp_add(struct scd_context *ctx, u32 addr, u32 id)
{
   static const struct gpio_cfg qsfp_gpios[] = {
      {0, true,  true,  false, "interrupt"},
      {2, true,  true,  false, "present"},
      {3, true,  false, true,  "interrupt_changed"},
      {5, true,  false, true,  "present_changed"},
      {6, false, false, false, "lp_mode"},
      {7, false, false, false, "reset"},
      {8, false, true,  false, "modsel"},
   };

   scd_dbg("qsfp %u @ 0x%04x\n", id, addr);
   return scd_xcvr_add(ctx, "qsfp", qsfp_gpios, ARRAY_SIZE(qsfp_gpios), addr, id);
}

static int scd_xcvr_osfp_add(struct scd_context *ctx, u32 addr, u32 id)
{
   static const struct gpio_cfg osfp_gpios[] = {
      {0, true,  true,  false, "interrupt"},
      {2, true,  true,  false, "present"},
      {3, true,  false, true,  "interrupt_changed"},
      {5, true,  false, true,  "present_changed"},
      {6, false, false, false, "lp_mode"},
      {7, false, false, false, "reset"},
      {8, false, true,  false, "modsel"},
   };

   scd_dbg("osfp %u @ 0x%04x\n", id, addr);
   return scd_xcvr_add(ctx, "osfp", osfp_gpios, ARRAY_SIZE(osfp_gpios), addr, id);
}

static int scd_gpio_add(struct scd_context *ctx, const char *name,
                        u32 addr, u32 bitpos, bool read_only, bool active_low)
{
   int err;
   struct scd_gpio *gpio;

   gpio = kzalloc(sizeof(*gpio), GFP_KERNEL);
   if (!gpio) {
      return -ENOMEM;
   }

   snprintf(gpio->name, sizeof_field(typeof(*gpio), name), name);
   if (read_only)
      gpio->attr = (struct scd_gpio_attribute)SCD_RO_GPIO_ATTR(
                           gpio->name, ctx, addr, bitpos, active_low);
   else
      gpio->attr = (struct scd_gpio_attribute)SCD_RW_GPIO_ATTR(
                           gpio->name, ctx, addr, bitpos, active_low);

   err = scd_gpio_register(ctx, gpio);
   if (err) {
      kfree(gpio);
      return err;
   }

   return 0;
}

static int scd_reset_add(struct scd_context *ctx, const char *name,
                         u32 addr, u32 bitpos)
{
   int err;
   struct scd_reset *reset;

   reset = kzalloc(sizeof(*reset), GFP_KERNEL);
   if (!reset) {
      return -ENOMEM;
   }

   snprintf(reset->name, sizeof_field(typeof(*reset), name), name);
   reset->attr = (struct scd_reset_attribute)SCD_RESET_ATTR(
                                                reset->name, ctx, addr, bitpos);

   err = scd_reset_register(ctx, reset);
   if (err) {
      kfree(reset);
      return err;
   }
   return 0;
}

#define PARSE_INT_OR_RETURN(Buf, Tmp, Type, Ptr)        \
   do {                                                 \
      int ___ret = 0;                                   \
      Tmp = strsep(Buf, " ");                           \
      if (!Tmp || !*Tmp) {                              \
         return -EINVAL;                                \
      }                                                 \
      ___ret = kstrto##Type(Tmp, 0, Ptr);               \
      if (___ret) {                                     \
         return ___ret;                                 \
      }                                                 \
   } while(0)

#define PARSE_ADDR_OR_RETURN(Buf, Tmp, Type, Ptr, Size) \
   do {                                                 \
      PARSE_INT_OR_RETURN(Buf, Tmp, Type, Ptr);         \
      if (*(Ptr) > (Size)) {                            \
         return -EINVAL;                                \
      }                                                 \
   } while(0)

#define PARSE_STR_OR_RETURN(Buf, Tmp, Ptr)              \
   do {                                                 \
      Tmp = strsep(Buf, " ");                           \
      if (!Tmp || !*Tmp) {                              \
         return -EINVAL;                                \
      }                                                 \
      Ptr = Tmp;                                        \
   } while(0)

#define PARSE_END_OR_RETURN(Buf, Tmp)                   \
   do {                                                 \
      Tmp = strsep(Buf, " ");                           \
      if (Tmp) {                                        \
         return -EINVAL;                                \
      }                                                 \
   } while(0)


// new_smbus_master <addr> <accel_id> <bus_count:8>
static ssize_t parse_new_object_smbus_master(struct scd_context *ctx,
                                             char *buf, size_t count)
{
   u32 id;
   u32 addr;
   u32 bus_count = MASTER_DEFAULT_BUS_COUNT;

   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &id);

   tmp = strsep(&buf, " ");
   if (tmp && *tmp) {
      res = kstrtou32(tmp, 0, &bus_count);
      if (res)
         return res;
      PARSE_END_OR_RETURN(&buf, tmp);
   }

   res = scd_smbus_master_add(ctx, addr, id, bus_count);
   if (res)
      return res;

   return count;
}

// new_mdio_device <master> <bus> <id> <portAddr> <devAddr> <clause>
static ssize_t parse_new_object_mdio_device(struct scd_context *ctx,
                                            char *buf, size_t count)
{
   u16 master;
   u16 bus;
   u16 id;
   u16 prtad;
   u16 devad;
   u16 clause;
   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_INT_OR_RETURN(&buf, tmp, u16, &master);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &bus);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &id);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &prtad);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &devad);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &clause);
   PARSE_END_OR_RETURN(&buf, tmp);

   res = scd_mdio_device_add(ctx, master, bus, id, prtad, devad, clause);
   if (res)
      return res;

   return count;
}

// new_mdio_master <addr> <id> <bus_count> <speed>
static ssize_t parse_new_object_mdio_master(struct scd_context *ctx,
                                            char *buf, size_t count)
{
   u32 addr;
   u16 id;
   u16 bus_count;
   u16 bus_speed;
   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &id);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &bus_count);
   PARSE_INT_OR_RETURN(&buf, tmp, u16, &bus_speed);
   PARSE_END_OR_RETURN(&buf, tmp);

   res = scd_mdio_master_add(ctx, addr, id, bus_count, bus_speed);
   if (res)
      return res;

   return count;
}

// new_led <addr> <name>
static ssize_t parse_new_object_led(struct scd_context *ctx,
                                    char *buf, size_t count)
{
   u32 addr;
   const char *name;

   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_STR_OR_RETURN(&buf, tmp, name);
   PARSE_END_OR_RETURN(&buf, tmp);

   res = scd_led_add(ctx, name, addr);
   if (res)
      return res;

   return count;
}

enum xcvr_type {
   XCVR_TYPE_SFP,
   XCVR_TYPE_QSFP,
   XCVR_TYPE_OSFP,
};

static ssize_t parse_new_object_xcvr(struct scd_context *ctx, enum xcvr_type type,
                                     char *buf, size_t count)
{
   u32 addr;
   u32 id;

   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &id);
   PARSE_END_OR_RETURN(&buf, tmp);

   if (type == XCVR_TYPE_SFP)
      res = scd_xcvr_sfp_add(ctx, addr, id);
   else if (type == XCVR_TYPE_QSFP)
      res = scd_xcvr_qsfp_add(ctx, addr, id);
   else if (type == XCVR_TYPE_OSFP)
      res = scd_xcvr_osfp_add(ctx, addr, id);
   else
      res = -EINVAL;

   if (res)
      return res;

   return count;
}

// new_osfp <addr> <id>
static ssize_t parse_new_object_osfp(struct scd_context *ctx,
                                     char *buf, size_t count)
{
   return parse_new_object_xcvr(ctx, XCVR_TYPE_OSFP, buf, count);
}

// new_qsfp <addr> <id>
static ssize_t parse_new_object_qsfp(struct scd_context *ctx,
                                     char *buf, size_t count)
{
   return parse_new_object_xcvr(ctx, XCVR_TYPE_QSFP, buf, count);
}

// new_sfp <addr> <id>
static ssize_t parse_new_object_sfp(struct scd_context *ctx,
                                     char *buf, size_t count)
{
   return parse_new_object_xcvr(ctx, XCVR_TYPE_SFP, buf, count);
}

// new_reset <addr> <name> <bitpos>
static ssize_t parse_new_object_reset(struct scd_context *ctx,
                                      char *buf, size_t count)
{
   u32 addr;
   const char *name;
   u32 bitpos;

   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_STR_OR_RETURN(&buf, tmp, name);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &bitpos);
   PARSE_END_OR_RETURN(&buf, tmp);

   res = scd_reset_add(ctx, name, addr, bitpos);
   if (res)
      return res;

   return count;
}

// new_fan_group <addr> <platform> <fan_count>
static ssize_t parse_new_object_fan_group(struct scd_context *ctx,
                                          char *buf, size_t count)
{
   const char *tmp;
   u32 addr;
   u32 platform_id;
   u32 fan_count;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &platform_id);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &fan_count);
   PARSE_END_OR_RETURN(&buf, tmp);

   res = scd_fan_group_add(ctx, addr, platform_id, fan_count);
   if (res)
      return res;

   return count;
}

// new_gpio <addr> <name> <bitpos> <ro> <activeLow>
static ssize_t parse_new_object_gpio(struct scd_context *ctx,
                                     char *buf, size_t count)
{
   u32 addr;
   const char *name;
   u32 bitpos;
   u32 read_only;
   u32 active_low;

   const char *tmp;
   int res;

   if (!buf)
      return -EINVAL;

   PARSE_ADDR_OR_RETURN(&buf, tmp, u32, &addr, ctx->res_size);
   PARSE_STR_OR_RETURN(&buf, tmp, name);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &bitpos);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &read_only);
   PARSE_INT_OR_RETURN(&buf, tmp, u32, &active_low);
   PARSE_END_OR_RETURN(&buf, tmp);

   res = scd_gpio_add(ctx, name, addr, bitpos, read_only, active_low);
   if (res)
      return res;

   return count;
}

typedef ssize_t (*new_object_parse_func)(struct scd_context*, char*, size_t);
static struct {
   const char *name;
   new_object_parse_func func;
} funcs[] = {
   { "fan_group",       parse_new_object_fan_group},
   { "gpio",            parse_new_object_gpio },
   { "led",             parse_new_object_led },
   { "mdio_device",     parse_new_object_mdio_device },
   { "mdio_master",     parse_new_object_mdio_master },
   { "osfp",            parse_new_object_osfp },
   { "qsfp",            parse_new_object_qsfp },
   { "reset",           parse_new_object_reset },
   { "sfp",             parse_new_object_sfp },
   { "smbus_master",    parse_new_object_smbus_master },
   { NULL, NULL }
};

static ssize_t parse_new_object(struct scd_context *ctx, const char *buf,
                                size_t count)
{
   char tmp[MAX_CONFIG_LINE_SIZE];
   char *ptr = tmp;
   char *tok;
   int i = 0;
   ssize_t err;

   if (count >= MAX_CONFIG_LINE_SIZE) {
      scd_warn("new_object line is too long\n");
      return -EINVAL;
   }

   strncpy(tmp, buf, count);
   tmp[count] = 0;
   tok = strsep(&ptr, " ");
   if (!tok)
      return -EINVAL;

   while (funcs[i].name) {
      if (!strcmp(tok, funcs[i].name))
         break;
      i++;
   }

   if (!funcs[i].name)
      return -EINVAL;

   err = funcs[i].func(ctx, ptr, count - (ptr - tmp));
   if (err < 0)
      return err;

   return count;
}

typedef ssize_t (*line_parser_func)(struct scd_context *ctx, const char *buf,
   size_t count);

static ssize_t parse_lines(struct scd_context *ctx, const char *buf,
                           size_t count, line_parser_func parser)
{
   ssize_t res;
   size_t left = count;
   const char *nl;

   if (count == 0)
      return 0;

   while (true) {
      nl = strnchr(buf, left, '\n');
      if (!nl)
         nl = buf + left; // points on the \0

      res = parser(ctx, buf, nl - buf);
      if (res < 0)
         return res;
      left -= res;

      buf = nl;
      while (left && *buf == '\n') {
         buf++;
         left--;
      }
      if (!left)
         break;
   }

   return count;
}

static ssize_t new_object(struct device *dev, struct device_attribute *attr,
                          const char *buf, size_t count)
{
   ssize_t res;
   struct scd_context *ctx = get_context_for_dev(dev);

   if (!ctx) {
      return -ENODEV;
   }

   scd_lock(ctx);
   if (ctx->initialized) {
      scd_unlock(ctx);
      return -EBUSY;
   }
   res = parse_lines(ctx, buf, count, parse_new_object);
   scd_unlock(ctx);
   return res;
}

static DEVICE_ATTR(new_object, S_IWUSR|S_IWGRP, 0, new_object);

static ssize_t parse_smbus_tweak(struct scd_context *ctx, const char *buf,
                                 size_t count)
{
   char buf_copy[MAX_CONFIG_LINE_SIZE];
   struct bus_params params;
   ssize_t err;
   char *ptr = buf_copy;
   const char *tmp;
   u16 bus;

   if (count >= MAX_CONFIG_LINE_SIZE) {
      scd_warn("smbus_tweak line is too long\n");
      return -EINVAL;
   }

   strncpy(buf_copy, buf, count);
   buf_copy[count] = 0;

   PARSE_INT_OR_RETURN(&ptr, tmp, u16, &bus);
   PARSE_INT_OR_RETURN(&ptr, tmp, u16, &params.addr);
   PARSE_INT_OR_RETURN(&ptr, tmp, u8, &params.t);
   PARSE_INT_OR_RETURN(&ptr, tmp, u8, &params.datr);
   PARSE_INT_OR_RETURN(&ptr, tmp, u8, &params.datw);
   PARSE_INT_OR_RETURN(&ptr, tmp, u8, &params.ed);

   err = scd_set_smbus_params(ctx, bus, &params);
   if (err == 0)
      return count;
   return err;
}

static ssize_t smbus_tweaks(struct device *dev, struct device_attribute *attr,
                            const char *buf, size_t count)
{
   ssize_t res;
   struct scd_context *ctx = get_context_for_dev(dev);

   if (!ctx) {
      return -ENODEV;
   }

   scd_lock(ctx);
   res = parse_lines(ctx, buf, count, parse_smbus_tweak);
   scd_unlock(ctx);
   return res;
}

static ssize_t scd_dump_smbus_tweaks(struct scd_context *ctx, char *buf, size_t max)
{
   const struct scd_smbus_master *master;
   const struct scd_smbus *bus;
   const struct bus_params *params;
   ssize_t count = 0;

   list_for_each_entry(master, &ctx->smbus_master_list, list) {
      list_for_each_entry(bus, &master->bus_list, list) {
         list_for_each_entry(params, &bus->params, list) {
            count += scnprintf(buf + count, max - count,
                  "%d/%d/%02x: adap=%d t=%d datr=%d datw=%d ed=%d\n",
                  master->id, bus->id, params->addr, bus->adap.nr,
                  params->t, params->datr, params->datw, params->ed);
            if (count == max) {
               return count;
            }
         }
      }
   }

   return count;
}

static ssize_t show_smbus_tweaks(struct device *dev, struct device_attribute *attr,
                                 char *buf)
{
   struct scd_context *ctx = get_context_for_dev(dev);
   ssize_t count;

   if (!ctx) {
      return -ENODEV;
   }

   scd_lock(ctx);
   count = scd_dump_smbus_tweaks(ctx, buf, PAGE_SIZE);
   scd_unlock(ctx);

   return count;
}

static DEVICE_ATTR(smbus_tweaks, S_IRUSR|S_IRGRP|S_IWUSR|S_IWGRP,
                   show_smbus_tweaks, smbus_tweaks);

static int scd_create_sysfs_files(struct scd_context *ctx) {
   int err;

   err = sysfs_create_file(get_scd_kobj(ctx), &dev_attr_new_object.attr);
   if (err) {
      dev_err(get_scd_dev(ctx), "could not create %s attribute: %d",
              dev_attr_new_object.attr.name, err);
      goto fail_new_object;
   }

   err = sysfs_create_file(get_scd_kobj(ctx), &dev_attr_smbus_tweaks.attr);
   if (err) {
      dev_err(get_scd_dev(ctx), "could not create %s attribute for smbus tweak: %d",
              dev_attr_smbus_tweaks.attr.name, err);
      goto fail_smbus_tweaks;
   }

   return 0;

fail_smbus_tweaks:
   sysfs_remove_file(get_scd_kobj(ctx), &dev_attr_new_object.attr);
fail_new_object:
   return err;
}

static int scd_ext_hwmon_probe(struct pci_dev *pdev, size_t mem_len)
{
   struct scd_context *ctx = get_context_for_pdev(pdev);
   int err;

   if (ctx) {
      scd_warn("this pci device has already been probed\n");
      return -EEXIST;
   }

   ctx = kzalloc(sizeof(*ctx), GFP_KERNEL);
   if (!ctx) {
      return -ENOMEM;
   }

   ctx->pdev = pdev;
   get_device(&pdev->dev);
   INIT_LIST_HEAD(&ctx->list);

   ctx->initialized = false;
   mutex_init(&ctx->mutex);

   ctx->res_size = mem_len;

   INIT_LIST_HEAD(&ctx->led_list);
   INIT_LIST_HEAD(&ctx->smbus_master_list);
   INIT_LIST_HEAD(&ctx->mdio_master_list);
   INIT_LIST_HEAD(&ctx->gpio_list);
   INIT_LIST_HEAD(&ctx->reset_list);
   INIT_LIST_HEAD(&ctx->xcvr_list);
   INIT_LIST_HEAD(&ctx->fan_group_list);

   kobject_get(&pdev->dev.kobj);

   module_lock();
   list_add_tail(&ctx->list, &scd_list);
   module_unlock();

   err = scd_create_sysfs_files(ctx);
   if (err) {
      goto fail_sysfs;
   }

   return 0;

fail_sysfs:
   module_lock();
   list_del(&ctx->list);
   module_unlock();

   kobject_put(&pdev->dev.kobj);
   kfree(ctx);
   put_device(&pdev->dev);

   return err;
}

static void scd_ext_hwmon_remove(struct pci_dev *pdev)
{
   struct scd_context *ctx = get_context_for_pdev(pdev);

   if (!ctx) {
      return;
   }

   scd_info("removing scd components\n");

   scd_lock(ctx);
   scd_smbus_remove_all(ctx);
   scd_mdio_remove_all(ctx);
   scd_led_remove_all(ctx);
   scd_gpio_remove_all(ctx);
   scd_reset_remove_all(ctx);
   scd_xcvr_remove_all(ctx);
   scd_fan_group_remove_all(ctx);
   scd_unlock(ctx);

   module_lock();
   list_del(&ctx->list);
   module_unlock();

   sysfs_remove_file(&pdev->dev.kobj, &dev_attr_new_object.attr);
   sysfs_remove_file(&pdev->dev.kobj, &dev_attr_smbus_tweaks.attr);

   kfree(ctx);

   kobject_put(&pdev->dev.kobj);
   put_device(&pdev->dev);
}

static int scd_ext_hwmon_init_trigger(struct pci_dev *pdev)
{
   struct scd_context *ctx = get_context_for_pdev(pdev);

   if (!ctx) {
      return -ENODEV;
   }

   scd_lock(ctx);
   ctx->initialized = true;
   scd_unlock(ctx);
   return 0;
}

static struct scd_ext_ops scd_hwmon_ops = {
   .probe  = scd_ext_hwmon_probe,
   .remove = scd_ext_hwmon_remove,
   .init_trigger = scd_ext_hwmon_init_trigger,
};

static int __init scd_hwmon_init(void)
{
   int err = 0;

   scd_info("loading scd hwmon driver\n");
   mutex_init(&scd_hwmon_mutex);
   INIT_LIST_HEAD(&scd_list);

   err = scd_register_ext_ops(&scd_hwmon_ops);
   if (err) {
      scd_warn("scd_register_ext_ops failed\n");
      return err;
   }

   return err;
}

static void __exit scd_hwmon_exit(void)
{
   scd_info("unloading scd hwmon driver\n");
   scd_unregister_ext_ops();
}

module_init(scd_hwmon_init);
module_exit(scd_hwmon_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Arista Networks");
MODULE_DESCRIPTION("SCD component driver");
