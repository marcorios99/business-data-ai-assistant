# Dataset sintético

El generador crea datos empresariales sintéticos para la compañía ficticia de retail y
distribución. No representa clientes, proveedores ni transacciones reales.

Los datos maestros son deterministas: la misma combinación de `--scale` y `--seed`
produce el mismo conjunto de datos. El perfil `demo` es el predeterminado; también están
definidos `portfolio` y `stress` para escalas posteriores.

```powershell
python scripts/generate_dataset.py --scale demo --seed 2026 --force
```

Actualmente se generan tiendas, almacenes, empleados, categorías, marcas, productos,
proveedores, relaciones proveedor-producto, segmentos de clientes y clientes. La base se
valida después de insertar los maestros.

Ventas, pagos, promociones aplicadas, compras, inventario, devoluciones, objetivos y
patrones temporales llegarán en hitos posteriores.
