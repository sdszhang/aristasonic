/* Copyright (c) 2020 Arista Networks, Inc.
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

#ifndef _LINUX_DRIVER_SCD_HWMON_H_
#define _LINUX_DRIVER_SCD_HWMON_H_

#include <linux/printk.h>

#define scd_err(fmt, ...) \
   pr_err("scd-hwmon: " fmt, ##__VA_ARGS__);
#define scd_warn(fmt, ...) \
   pr_warn("scd-hwmon: " fmt, ##__VA_ARGS__);
#define scd_info(fmt, ...) \
   pr_info("scd-hwmon: " fmt, ##__VA_ARGS__);
#define scd_dbg(fmt, ...) \
   pr_debug("scd-hwmon: " fmt, ##__VA_ARGS__);

struct scd_context {
   struct pci_dev *pdev;
   size_t res_size;

   struct list_head list;

   struct mutex mutex;
   bool initialized;

   struct list_head gpio_list;
   struct list_head reset_list;
   struct list_head led_list;
   struct list_head smbus_master_list;
   struct list_head mdio_master_list;
   struct list_head xcvr_list;
   struct list_head fan_group_list;
};

#endif /* !_LINUX_DRIVER_SCD_HWMON_H_ */
