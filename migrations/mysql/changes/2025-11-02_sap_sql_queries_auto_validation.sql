-- ================================================================
-- SAP B1 SQL Queries Auto-Validation Feature
-- Date: 2025-11-02
-- ================================================================
-- This migration documents the SAP B1 SQL Queries that are
-- automatically validated and created on application startup.
--
-- The application uses sap_query_manager.py to check if these
-- queries exist in SAP B1 database and creates them if missing.
--
-- These queries are stored in SAP B1's SQLQueries table and are
-- used throughout the WMS application for various operations.
-- ================================================================

-- NOTE: These are SAP B1 Service Layer queries, not MySQL queries
-- They are automatically managed by the application via SAP B1 API
-- This file serves as documentation and reference

-- ================================================================
-- 1. Item Validation Queries
-- ================================================================

-- ItemCode_Validation
-- Purpose: Validate serial number items with warehouse availability
-- Parameters: :item_code, :whcode
-- Returns: ItemCode, itemName, DistNumber (Serial), WhsCode
/*
{
   "SqlCode":"ItemCode_Validation",
   "SqlName":"ItemCode_Validation",
   "SqlText":"SELECT T0.[ItemCode],T0.[itemName], T0.[DistNumber], T1.[WhsCode] FROM [OSRN] T0  INNER JOIN [OSRQ] T1 ON T0.[AbsEntry] =T1.[MdAbsEntry] WHERE  T1.[Quantity] >'0' AND T0.[ItemCode]=:item_code AND T1.[WhsCode]=:whcode"
}
*/

-- ItemCode_Batch_Serial_Val
-- Purpose: Get item management type (Batch, Serial, None)
-- Parameters: :itemCode
-- Returns: ItemCode, BatchNum flag, SerialNum flag, NonBatch_NonSerialMethod
/*
{
   "SqlCode":"ItemCode_Batch_Serial_Val",
   "SqlName":"ItemCode_Batch_Serial_Val",
   "SqlText":"Select T0.[ItemCode], IsNULL(T0.[ManBtchNum],'N') as [BatchNum] ,IsNULL(T0.[ManSerNum],'N') as [SerialNum],IsNULL(T0.[MngMethod],'N')  as [NonBatch_NonSerialMethod] FROM [OITM] T0 WHERE T0.[ItemCode]=:itemCode"
}
*/

-- ================================================================
-- 2. Inventory Queries by Management Type
-- ================================================================

-- GetSerialManagedItemWH
-- Purpose: Get serial-managed items with warehouse availability
-- Parameters: :itemCode
-- Returns: itemCode, SerialNumber, WarehouseCode, WarehouseName, AvailableQty, SysNumber
/*
{
   "SqlCode":"GetSerialManagedItemWH",
   "SqlName":"GetSerialManagedItemWH1",
   "SqlText":"SELECT DISTINCT OSRN.[ItemCode] AS [itemCode], OSRN.[DistNumber] AS [SerialNumber], OSRQ.[WhsCode] AS [WarehouseCode], OWHS.[WhsName] AS [WarehouseName], OSRQ.[Quantity] AS [AvailableQty], OSRN.[SysNumber] FROM [OSRN] AS OSRN INNER JOIN [OSRQ] AS OSRQ ON OSRN.[SysNumber] = OSRQ.[SysNumber] AND OSRN.[ItemCode] = OSRQ.[ItemCode] INNER JOIN [OWHS] AS OWHS ON OSRQ.[WhsCode] = OWHS.[WhsCode] WHERE OSRN.[ItemCode] = :itemCode AND OSRQ.[Quantity] > 0 ORDER BY OSRN.[DistNumber]"
}
*/

-- GetBatchManagedItemWH
-- Purpose: Get batch-managed items with warehouse availability
-- Parameters: :itemCode
-- Returns: itemCode, BatchNumber, WarehouseCode, WarehouseName, AvailableQty, SysNumber
/*
{
   "SqlCode":"GetBatchManagedItemWH",
   "SqlName":"GetBatchManagedItemWH",
   "SqlText":"SELECT DISTINCT OBTN.[ItemCode] AS [itemCode], OBTN.[DistNumber] AS [BatchNumber], OBTQ.[WhsCode] AS [WarehouseCode], OWHS.[WhsName] AS [WarehouseName], OBTQ.[Quantity] AS [AvailableQty], OBTN.[SysNumber] FROM [OBTN] AS OBTN INNER JOIN [OBTQ] AS OBTQ ON OBTN.[SysNumber] = OBTQ.[SysNumber] AND OBTN.[ItemCode] = OBTQ.[ItemCode] INNER JOIN [OWHS] AS OWHS ON OBTQ.[WhsCode] = OWHS.[WhsCode] WHERE OBTN.[ItemCode] = :itemCode AND OBTQ.[Quantity] > 0 ORDER BY OBTN.[DistNumber]"
}
*/

-- GetNonSerialNonBatchManagedItemWH
-- Purpose: Get non-serial, non-batch items with warehouse availability
-- Parameters: :itemCode
-- Returns: ItemCode, ItemName, WarehouseCode, WarehouseName, AvailableQty
/*
{
   "SqlCode":"GetNonSerialNonBatchManagedItemWH",
   "SqlName":"GetNonSerialNonBatchManagedItemWH",
   "SqlText":"SELECT OITM.[ItemCode], OITM.[ItemName], OITW.[WhsCode] AS [WarehouseCode], OWHS.[WhsName] AS [WarehouseName], OITW.[OnHand] AS [AvailableQty] FROM [OITM] AS OITM INNER JOIN [OITW] AS OITW ON OITM.[ItemCode] = OITW.[ItemCode] INNER JOIN [OWHS] AS OWHS ON OITW.[WhsCode] = OWHS.[WhsCode] WHERE OITM.[ItemCode] = :itemCode AND OITW.[OnHand] > 0"
}
*/

-- ================================================================
-- 3. Document Series Queries
-- ================================================================

-- Get_SO_Series
-- Purpose: Get Sales Order document series
-- Parameters: None
-- Returns: SeriesName, Series
/*
{
   "SqlCode":"Get_SO_Series",
   "SqlName":"Get_SO_Series",
   "SqlText":"SELECT T0.[SeriesName], T0.[Series] FROM [NNM1] T0 WHERE T0.[ObjectCode] = '17'"
}
*/

-- Get_PO_Series
-- Purpose: Get Purchase Order document series
-- Parameters: None
-- Returns: Series, SeriesName
/*
{
   "SqlCode":"Get_PO_Series",
   "SqlName":"Get_PO_Series",
   "SqlText":"SELECT T0.[Series], T0.[SeriesName] FROM [NNM1] T0 WHERE T0.[ObjectCode] = '22' ORDER BY T0.[SeriesName]"
}
*/

-- Get_INVT_Series
-- Purpose: Get Inventory Transfer document series
-- Parameters: None
-- Returns: Series, SeriesName
-- ObjectCode: 1250000001 = Inventory Transfer
/*
{
   "SqlCode":"Get_INVT_Series",
   "SqlName":"Get_INVT_Series",
   "SqlText":"SELECT T0.[Series],T0.[SeriesName] FROM [NNM1] T0 WHERE T0.[ObjectCode] = '1250000001' ORDER BY T0.[SeriesName]"
}
*/

-- Get_INVCNT_Series
-- Purpose: Get Inventory Counting document series
-- Parameters: None
-- Returns: Series, SeriesName
-- ObjectCode: 1470000065 = Inventory Counting
/*
{
   "SqlCode":"Get_INVCNT_Series",
   "SqlName":"Get_INVCNT_Series",
   "SqlText":"SELECT n.[Series],n.[SeriesName] FROM [NNM1] n WHERE n.[ObjectCode] = '1470000065' ORDER BY n.[SeriesName]"
}
*/

-- ================================================================
-- 4. Document Lookup Queries
-- ================================================================

-- Get_SO_Details
-- Purpose: Get Sales Order DocEntry from DocNum and Series
-- Parameters: :SONumber, :Series
-- Returns: DocEntry
/*
{
   "SqlCode":"Get_SO_Details",
   "SqlName":"Get_SO_Details",
   "SqlText":"SELECT T0.[DocEntry] FROM [ORDR] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE T0.[DocNum] =:SONumber AND  T1.[Series]=:Series"
}
*/

-- Get_PO_DocEntry
-- Purpose: Get Purchase Order DocEntry from DocNum and Series
-- Parameters: :series, :docNum
-- Returns: DocEntry
/*
{
   "SqlCode":"Get_PO_DocEntry",
   "SqlName":"Get_PO_DocEntry",
   "SqlText":"SELECT [DocEntry] FROM [OPOR] WHERE [Series] =:series AND [DocNum] =:docNum"
}
*/

-- Get_INVT_DocEntry
-- Purpose: Get Inventory Transfer DocEntry
-- Parameters: :series, :docNum
-- Returns: DocEntry
/*
{
   "SqlCode":"Get_INVT_DocEntry",
   "SqlName":"Get_INVT_DocEntry",
   "SqlText":"SELECT T0.[DocEntry] FROM [OWTQ] T0 WHERE T0.[Series] = :series AND T0.[DocNum] = :docNum"
}
*/

-- Get_INVCNT_DocEntry
-- Purpose: Get Inventory Counting DocEntry
-- Parameters: :series, :docNum
-- Returns: DocEntry
/*
{
   "SqlCode":"Get_INVCNT_DocEntry",
   "SqlName":"Get_INVCNT_DocEntry",
   "SqlText":"SELECT C.[DocEntry] FROM [OINC] C INNER JOIN [NNM1] S ON C.[Series] = S.[Series] WHERE C.[Series] =:series AND C.[DocNum] =:docNum"
}
*/

-- ================================================================
-- 5. Open Document Queries
-- ================================================================

-- Get_Open_SO_DocNum
-- Purpose: Get open Sales Orders by series
-- Parameters: :series
-- Returns: DocEntry, DocNum, CardCode, CardName, DocStatus
/*
{
   "SqlCode":"Get_Open_SO_DocNum",
   "SqlName":"Get_Open_SO_DocNum",
   "SqlText":"SELECT T0.[DocEntry],T0.[DocNum],T0.[CardCode],T0.[CardName],T0.[DocStatus] FROM [ORDR] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE T0.[Series] = :series AND T0.[DocStatus] = 'O' ORDER BY T0.[DocEntry]"
}
*/

-- Get_Open_PO_DocNum
-- Purpose: Get open Purchase Orders by series
-- Parameters: :series
-- Returns: DocEntry, DocNum, Series, SeriesName, CardCode, CardName
/*
{
   "SqlCode":"Get_Open_PO_DocNum",
   "SqlName":"Get_Open_PO_DocNum",
   "SqlText":"SELECT T0.[DocEntry],T0.[DocNum],T0.[Series],T1.[SeriesName],T0.[CardCode],T0.[CardName] FROM [OPOR] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE  T0.[DocStatus] = 'O' AND T0.[Series] =:series ORDER BY T0.[DocNum]"
}
*/

-- Get_Open_INVTRNF_DocNum
-- Purpose: Get open Inventory Transfers by series
-- Parameters: :series
-- Returns: DocEntry, DocNum, Series, SeriesName
/*
{
   "SqlCode":"Get_Open_INVTRNF_DocNum",
   "SqlName":"Get_Open_INVTRNF_DocNum",
   "SqlText":"SELECT T0.[DocEntry],T0.[DocNum],T0.[Series],T1.[SeriesName] FROM [OWTQ] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE T0.[Series] =:series AND T0.[DocStatus] = 'O' ORDER BY T0.[DocNum]"
}
*/

-- Get_Open_INVCNT_DocNum
-- Purpose: Get open Inventory Counting documents by series
-- Parameters: :series
-- Returns: DocEntry, DocNum, SeriesName, CountDate, Status
/*
{
   "SqlCode":"Get_Open_INVCNT_DocNum",
   "SqlName":"Get_Open_INVCNT_DocNum",
   "SqlText":"SELECT T0.[DocEntry],T0.[DocNum],T1.[SeriesName],T0.[CountDate],T0.[Status] FROM [OINC] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] LEFT JOIN [OUSR] T2 ON T0.[UserSign] = T2.[USERID] WHERE T0.[Series] = :series AND T0.[Status] = 'O' ORDER BY T0.[CountDate] DESC, T0.[DocNum]"
}
*/

-- ================================================================
-- USAGE NOTES:
-- ================================================================
-- 1. These queries are automatically validated on app startup
-- 2. If a query is missing, it will be created via SAP B1 Service Layer API
-- 3. The sap_query_manager.py module handles all validation logic
-- 4. Queries use SAP B1 parameter syntax with :parameterName
-- 5. All queries are read-only (SELECT statements only)
-- 6. To add new queries, update the required_queries list in sap_query_manager.py
-- 7. Then document them here following the same format

-- ================================================================
-- MAINTENANCE:
-- ================================================================
-- When adding new SAP queries:
-- 1. Add to sap_query_manager.py required_queries list
-- 2. Document here with purpose, parameters, and returns
-- 3. Test the query in SAP B1 before deploying
-- 4. Update MIGRATION_LOG.md with the change
-- ================================================================
