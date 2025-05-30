import pyodbc
from previsiones.models import ArticuloPrevision
from django.db import IntegrityError
import logging
logger = logging.getLogger(__name__)

def importar_previsiones():
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER="
        "DATABASE=;"
        "UID=;"
        "PWD="
    )
    cursor = connection.cursor()

    query = """
    WITH Meses AS (
        SELECT DATEFROMPARTS(2024, 1, 1) AS Fecha
        UNION ALL
        SELECT DATEADD(MONTH, 1, Fecha) FROM Meses WHERE MONTH(Fecha) < 12
    ),
    IDsFamilias AS (
        SELECT id FROM (VALUES (1), (3), (4), (6), (98)) AS T(id)
    )

    SELECT
        LA.ARTICULO AS CODIGO,
        A.IDENTIFICACION,
        A.DESCRIPCION,
        CASE LA.ALMACEN
            WHEN 1 THEN 'MALLORCA'
            WHEN 2 THEN 'IBIZA'
            WHEN 3 THEN 'MENORCA'
            ELSE 'DESCONOCIDO'
        END AS ALMACEN,
        F.NOMBRE AS FAMILIA,
        SF.[nombre subfam] AS SUBFAMILIA,
        YEAR(M.Fecha) AS AÑO,
        MONTH(M.Fecha) AS MES,
        ISNULL(SUM(CASE 
            WHEN LA.TIPO_MOVIMIENTO = 51 AND LA.COD_PROVEEDOR NOT IN (713,730,733,734,1023,1047,1048,1256)
                 AND DATEPART(YEAR, LA.FECHA_MOVIMIENTO) = YEAR(M.Fecha)
                 AND DATEPART(MONTH, LA.FECHA_MOVIMIENTO) = MONTH(M.Fecha)
            THEN CAST(LA.CANTIDAD_OPERACION AS FLOAT)
            ELSE 0
        END), 0) AS CANTIDAD_COMPRA,
        ISNULL(SUM(CASE 
            WHEN LA.TIPO_MOVIMIENTO = 1 AND LA.COD_PROVEEDOR IS NULL AND LA.COD_CLIENTE IS NOT NULL
                 AND DATEPART(YEAR, LA.FECHA_MOVIMIENTO) = YEAR(M.Fecha)
                 AND DATEPART(MONTH, LA.FECHA_MOVIMIENTO) = MONTH(M.Fecha)
            THEN CAST(LA.CANTIDAD_OPERACION AS FLOAT)
            ELSE 0
        END), 0) AS PREVISION_VENTA,
        ISNULL(SUM(CASE 
            WHEN LA.TIPO_MOVIMIENTO = 1 AND LA.COD_PROVEEDOR IS NULL AND LA.COD_CLIENTE IS NOT NULL
                 AND DATEPART(YEAR, LA.FECHA_MOVIMIENTO) = YEAR(M.Fecha)
                 AND DATEPART(MONTH, LA.FECHA_MOVIMIENTO) = MONTH(M.Fecha)
            THEN 
                CASE A.FAMILIA
                    WHEN 1 THEN CAST(LA.CANTIDAD_OPERACION AS FLOAT) * 0.5
                    ELSE CAST(LA.CANTIDAD_OPERACION AS FLOAT) * 0.33
                END
            ELSE 0
        END), 0) AS STOCK_SEGURIDAD
    FROM Meses M
    JOIN [IMPORTMOCA].[dbo].[LINALMAC] LA ON DATEPART(YEAR, LA.FECHA_MOVIMIENTO) = YEAR(M.Fecha)
                                         AND DATEPART(MONTH, LA.FECHA_MOVIMIENTO) = MONTH(M.Fecha)
    LEFT JOIN [IMPORTMOCA].[dbo].[ARTICULO] A ON LA.ARTICULO = A.CODIGO
    LEFT JOIN [IMPORTMOCA].[dbo].[ARTICULO_FAMILIA] F ON A.FAMILIA = F.CODIGO
    LEFT JOIN [IMPORTMOCA].[dbo].[ARTICULO_SUBFAMILIAS] SF ON A.SUBFAMILIA = SF.[cod.subfam DANSAP]
    WHERE A.FAMILIA IN (SELECT id FROM IDsFamilias)
    GROUP BY
        LA.ARTICULO,
        A.IDENTIFICACION,
        A.DESCRIPCION,
        LA.ALMACEN,
        F.NOMBRE,
        SF.[nombre subfam],
        YEAR(M.Fecha),
        MONTH(M.Fecha)
    ORDER BY AÑO, MES, CODIGO
    OPTION (MAXRECURSION 0)
    """

    cursor.execute(query)
    columns = [col[0] for col in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    total = 0

    for row in rows:
        try:
            prevision_venta = abs(row['PREVISION_VENTA'] or 0)
            stock_seguridad = abs(row['STOCK_SEGURIDAD'] or 0)
            cantidad_stock_final = prevision_venta + stock_seguridad

            ArticuloPrevision.objects.update_or_create(
                codigo=row['CODIGO'],
                anio=row['AÑO'],
                mes=row['MES'],
                almacen=row['ALMACEN'],
                identificacion=row['IDENTIFICACION'] or '',
                defaults={
                    'identificacion': row['IDENTIFICACION'] or '',
                    'descripcion': row['DESCRIPCION'] or '',
                    'proveedor': '',  # No incluido por ahora
                    'familia': row['SUBFAMILIA'] or '',
                    'cantidad_compra': row['CANTIDAD_COMPRA'] or 0,
                    'prevision_venta': prevision_venta,
                    'stock_seguridad': stock_seguridad,
                    'cantidad_stock_final': cantidad_stock_final,
                }
            )
            total += 1
        except IntegrityError as e:
            logger.info(f"Error al insertar {row['CODIGO']}: {e}")

    logger.info(f"Importación completada: {total} registros guardados.")
