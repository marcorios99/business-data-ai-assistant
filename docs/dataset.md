# Dataset sintético

> **Legacy synthetic dataset:** this document describes the former SQLite prototype, not the current reference dataset. The project now uses WideWorldImporters on Microsoft SQL Server for text-to-SQL experiments. The generator remains temporarily as a historical artifact.

El generador crea datos empresariales sintéticos para la compañía ficticia de retail y
distribución. No representa clientes, proveedores ni transacciones reales.

Los datos maestros son deterministas: la misma combinación de `--scale` y `--seed`
produce el mismo conjunto de datos. El perfil `demo` es el predeterminado; también están
definidos `portfolio` y `stress` para escalas posteriores.

El período reproducible del dataset va de `2024-01-01` a `2026-07-31`. Las fechas de
maestros pueden ser anteriores a ese período, pero nunca posteriores a su fecha final.

```powershell
python scripts/generate_dataset.py --scale demo --seed 2026 --force
```

Actualmente se generan tiendas, almacenes, empleados, categorías, marcas, productos,
proveedores, relaciones proveedor-producto, segmentos de clientes y clientes. La base se
valida antes de confirmar la generación. Cada tienda recibe un Store Manager; los
proveedores mantienen perfiles consistentes de costo y lead time, y los clientes
empresariales reciben nombres ficticios de empresa.

Las ventas se simulan cronológicamente contra los movimientos de entrada disponibles. Una
línea vendida crea un movimiento `SALE` negativo desde un almacén con stock; no se permite
saldo histórico negativo. Las promociones aplican descuentos por porcentaje o por importe
fijo a la línea (el fijo se aplica una vez por línea). Subtotal menos descuento recibe IGV
de 18 %. El costo histórico es una aproximación del costo base; todavía no se modela FIFO.

También se generan órdenes de compra históricas, sus líneas y recepciones. Cada posición
de apertura se registra primero como un movimiento `INITIAL`; las cantidades recibidas se
registran como movimientos `PURCHASE` enlazados a la línea de compra. `inventory` es una
proyección reconstruida desde ese ledger, nunca una cantidad independiente. Los totales de
compra usan subtotal antes de IGV y 18 % de IGV calculado en céntimos.

Todavía no existen ventas, pagos, promociones aplicadas, devoluciones, objetivos ni
movimientos de salida. Por ello el inventario de este estado intermedio puede crecer con
las compras; la simulación cronológica completa llegará en los siguientes hitos.
