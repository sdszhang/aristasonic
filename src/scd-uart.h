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

#ifndef _LINUX_DRIVER_SCD_UART_H_
#define _LINUX_DRIVER_SCD_UART_H_

#include <linux/serial.h>
#include <linux/serial_core.h>

struct scd_context;

struct scd_uart {
   struct uart_driver driver;

   struct list_head port_list;

   bool initialized;
};

struct scd_uart_port {
   struct scd_uart *uart;
   struct list_head list;

   struct uart_port port;
   u32 addr_rx;
   u32 addr_tx;
   u32 id;
   speed_t baud;
};

#define PORT_SCD 42 // Value available in include/uapi/linux/serial_core.h
#define SCD_UART_FIFO_DEPTH 120
#define SCD_UART_MAX_PORT_NR 16

#define SCD_UART_RX_ADDR_OFFSET 0
#define SCD_UART_TX_ADDR_OFFSET 0x100


extern int scd_uart_add(struct scd_context *ctx, u32 addr, u32 id);
extern void scd_uart_remove_all(struct scd_context *ctx);

#endif /* !_LINUX_DRIVER_SCD_UART_H_ */
