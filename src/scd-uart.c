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

#include <linux/module.h>

#include "scd.h"
#include "scd-hwmon.h"
#include "scd-uart.h"

static void scd_uart_remove_port(struct scd_uart_port *port)
{
   uart_remove_one_port(&port->uart->driver, &port->port);
   list_del(&port->list);
   kfree(port);
}

void scd_uart_remove_all(struct scd_context *ctx)
{
   struct scd_uart *uart = &ctx->uart;
   struct scd_uart_port *port;
   struct scd_uart_port *tmp_port;

   if (!uart->initialized)
      return;

   list_for_each_entry_safe(port, tmp_port, &uart->port_list, list) {
      scd_uart_remove_port(port);
   }

   uart_unregister_driver(&uart->driver);
   uart->initialized = false;
}

static struct uart_ops scd_uart_ops = {
};

static int scd_uart_maybe_initialize(struct scd_context *ctx)
{
   struct scd_uart *uart = &ctx->uart;
   int res;

   if (uart->initialized)
      return 0;

   dev_dbg(get_scd_dev(ctx), "initializing uart context\n");

   uart->driver.owner = THIS_MODULE;
   uart->driver.driver_name = "scd-uart";
   uart->driver.dev_name = "ttySCD";
   uart->driver.nr = SCD_UART_MAX_PORT_NR;

   res = uart_register_driver(&uart->driver);
   if (res) {
      dev_err(get_scd_dev(ctx), "failed to register UART driver %d\n", res);
      return res;
   }

   INIT_LIST_HEAD(&uart->port_list);
   uart->initialized = true;

   return 0;
}

int scd_uart_add(struct scd_context *ctx, u32 addr, u32 id)
{
   struct scd_uart *uart = &ctx->uart;
   struct scd_uart_port *port;
   int err;

   err = scd_uart_maybe_initialize(ctx);
   if (err)
      return err;

   dev_dbg(get_scd_dev(ctx), "adding uart port %u at addr %#x\n", id, addr);

   port = kzalloc(sizeof(*port), GFP_KERNEL);
   if (!port)
      return -ENOMEM;

   port->uart = uart;
   port->addr_rx = addr + SCD_UART_RX_ADDR_OFFSET;
   port->addr_tx = addr + SCD_UART_TX_ADDR_OFFSET;
   port->id = id;
   port->baud = 9600;

   spin_lock_init(&port->port.lock);
   port->port.dev = get_scd_dev(ctx);
   port->port.irq = ctx->pdev->irq;
   port->port.line = id;
   port->port.type = PORT_SCD;
   port->port.ops = &scd_uart_ops;
   port->port.fifosize = SCD_UART_FIFO_DEPTH;
   port->port.iotype = UPIO_MEM;
   port->port.flags = UPF_BOOT_AUTOCONF;

   err = uart_add_one_port(&uart->driver, &port->port);
   if (err) {
      dev_err(get_scd_dev(ctx), "failed to register UART port %u: %d\n", id, err);
      goto fail_add;
   }

   list_add_tail(&port->list, &uart->port_list);

   return 0;

fail_add:
   kfree(port);

   return err;
}
