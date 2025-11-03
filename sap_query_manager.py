"""
SAP B1 SQL Query Manager
Validates and creates required SQL queries in SAP B1 database on application startup
"""

import logging
import requests
import urllib3

# Disable SSL warnings for SAP B1 connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SAPQueryManager:
    """Manages SAP B1 SQL Queries - validates existence and creates if missing"""
    
    def __init__(self, server_url, username, password, company_db):
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.company_db = company_db
        self.session_id = None
        self.logger = logging.getLogger(__name__)
        
        self.required_queries = [
            {
                "SqlCode": "ItemCode_Validation",
                "SqlName": "ItemCode_Validation",
                "SqlText": "SELECT T0.[ItemCode],T0.[itemName], T0.[DistNumber], T1.[WhsCode] FROM [OSRN] T0  INNER JOIN [OSRQ] T1 ON T0.[AbsEntry] =T1.[MdAbsEntry] WHERE  T1.[Quantity] >'0' AND T0.[ItemCode]=:item_code AND T1.[WhsCode]=:whcode"
            },
            {
                "SqlCode": "ItemCode_Batch_Serial_Val",
                "SqlName": "ItemCode_Batch_Serial_Val",
                "SqlText": "Select T0.[ItemCode], IsNULL(T0.[ManBtchNum],'N') as [BatchNum] ,IsNULL(T0.[ManSerNum],'N') as [SerialNum],IsNULL(T0.[MngMethod],'N')  as [NonBatch_NonSerialMethod] FROM [OITM] T0 WHERE T0.[ItemCode]=:itemCode"
            },
            {
                "SqlCode": "GetSerialManagedItemWH",
                "SqlName": "GetSerialManagedItemWH1",
                "SqlText": "SELECT DISTINCT OSRN.[ItemCode] AS [itemCode], OSRN.[DistNumber] AS [SerialNumber], OSRQ.[WhsCode] AS [WarehouseCode], OWHS.[WhsName] AS [WarehouseName], OSRQ.[Quantity] AS [AvailableQty], OSRN.[SysNumber] FROM [OSRN] AS OSRN INNER JOIN [OSRQ] AS OSRQ ON OSRN.[SysNumber] = OSRQ.[SysNumber] AND OSRN.[ItemCode] = OSRQ.[ItemCode] INNER JOIN [OWHS] AS OWHS ON OSRQ.[WhsCode] = OWHS.[WhsCode] WHERE OSRN.[ItemCode] = :itemCode AND OSRQ.[Quantity] > 0 ORDER BY OSRN.[DistNumber]"
            },
            {
                "SqlCode": "GetNonSerialNonBatchManagedItemWH",
                "SqlName": "GetNonSerialNonBatchManagedItemWH",
                "SqlText": "SELECT OITM.[ItemCode], OITM.[ItemName], OITW.[WhsCode] AS [WarehouseCode], OWHS.[WhsName] AS [WarehouseName], OITW.[OnHand] AS [AvailableQty] FROM [OITM] AS OITM INNER JOIN [OITW] AS OITW ON OITM.[ItemCode] = OITW.[ItemCode] INNER JOIN [OWHS] AS OWHS ON OITW.[WhsCode] = OWHS.[WhsCode] WHERE OITM.[ItemCode] = :itemCode AND OITW.[OnHand] > 0"
            },
            {
                "SqlCode": "GetBatchManagedItemWH",
                "SqlName": "GetBatchManagedItemWH",
                "SqlText": "SELECT DISTINCT OBTN.[ItemCode] AS [itemCode], OBTN.[DistNumber] AS [BatchNumber], OBTQ.[WhsCode] AS [WarehouseCode], OWHS.[WhsName] AS [WarehouseName], OBTQ.[Quantity] AS [AvailableQty], OBTN.[SysNumber] FROM [OBTN] AS OBTN INNER JOIN [OBTQ] AS OBTQ ON OBTN.[SysNumber] = OBTQ.[SysNumber] AND OBTN.[ItemCode] = OBTQ.[ItemCode] INNER JOIN [OWHS] AS OWHS ON OBTQ.[WhsCode] = OWHS.[WhsCode] WHERE OBTN.[ItemCode] = :itemCode AND OBTQ.[Quantity] > 0 ORDER BY OBTN.[DistNumber]"
            },
            {
                "SqlCode": "Get_SO_Series",
                "SqlName": "Get_SO_Series",
                "SqlText": "SELECT T0.[SeriesName], T0.[Series] FROM [NNM1] T0 WHERE T0.[ObjectCode] = '17'"
            },
            {
                "SqlCode": "Get_SO_Details",
                "SqlName": "Get_SO_Details",
                "SqlText": "SELECT T0.[DocEntry] FROM [ORDR] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE T0.[DocNum] =:SONumber AND  T1.[Series]=:Series"
            },
            {
                "SqlCode": "Get_PO_Series",
                "SqlName": "Get_PO_Series",
                "SqlText": "SELECT T0.[Series], T0.[SeriesName] FROM [NNM1] T0 WHERE T0.[ObjectCode] = '22' ORDER BY T0.[SeriesName]"
            },
            {
                "SqlCode": "Get_PO_DocEntry",
                "SqlName": "Get_PO_DocEntry",
                "SqlText": "SELECT [DocEntry] FROM [OPOR] WHERE [Series] =:series AND [DocNum] =:docNum"
            },
            {
                "SqlCode": "Get_Open_SO_DocNum",
                "SqlName": "Get_Open_SO_DocNum",
                "SqlText": "SELECT T0.[DocEntry],T0.[DocNum],T0.[CardCode],T0.[CardName],T0.[DocStatus] FROM [ORDR] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE T0.[Series] = :series AND T0.[DocStatus] = 'O' ORDER BY T0.[DocEntry]"
            },
            {
                "SqlCode": "Get_Open_PO_DocNum",
                "SqlName": "Get_Open_PO_DocNum",
                "SqlText": "SELECT T0.[DocEntry],T0.[DocNum],T0.[Series],T1.[SeriesName],T0.[CardCode],T0.[CardName] FROM [OPOR] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE  T0.[DocStatus] = 'O' AND T0.[Series] =:series ORDER BY T0.[DocNum]"
            },
            {
                "SqlCode": "Get_Open_INVTRNF_DocNum",
                "SqlName": "Get_Open_INVTRNF_DocNum",
                "SqlText": "SELECT T0.[DocEntry],T0.[DocNum],T0.[Series],T1.[SeriesName] FROM [OWTQ] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] WHERE T0.[Series] =:series AND T0.[DocStatus] = 'O' ORDER BY T0.[DocNum]"
            },
            {
                "SqlCode": "Get_Open_INVCNT_DocNum",
                "SqlName": "Get_Open_INVCNT_DocNum",
                "SqlText": "SELECT T0.[DocEntry],T0.[DocNum],T1.[SeriesName],T0.[CountDate],T0.[Status] FROM [OINC] T0 INNER JOIN [NNM1] T1 ON T0.[Series] = T1.[Series] LEFT JOIN [OUSR] T2 ON T0.[UserSign] = T2.[USERID] WHERE T0.[Series] = :series AND T0.[Status] = 'O' ORDER BY T0.[CountDate] DESC, T0.[DocNum]"
            },
            {
                "SqlCode": "Get_INVT_DocEntry",
                "SqlName": "Get_INVT_DocEntry",
                "SqlText": "SELECT T0.[DocEntry] FROM [OWTQ] T0 WHERE T0.[Series] = :series AND T0.[DocNum] = :docNum"
            },
            {
                "SqlCode": "Get_INVT_Series",
                "SqlName": "Get_INVT_Series",
                "SqlText": "SELECT T0.[Series],T0.[SeriesName] FROM [NNM1] T0 WHERE T0.[ObjectCode] = '1250000001' ORDER BY T0.[SeriesName]"
            },
            {
                "SqlCode": "Get_INVCNT_DocEntry",
                "SqlName": "Get_INVCNT_DocEntry",
                "SqlText": "SELECT C.[DocEntry] FROM [OINC] C INNER JOIN [NNM1] S ON C.[Series] = S.[Series] WHERE C.[Series] =:series AND C.[DocNum] =:docNum"
            },
            {
                "SqlCode": "Get_INVCNT_Series",
                "SqlName": "Get_INVCNT_Series",
                "SqlText": "SELECT n.[Series],n.[SeriesName] FROM [NNM1] n WHERE n.[ObjectCode] = '1470000065' ORDER BY n.[SeriesName]"
            }
        ]
    
    def login(self):
        """Login to SAP B1 and get session ID"""
        try:
            login_url = f"{self.server_url}/b1s/v1/Login"
            payload = {
                "CompanyDB": self.company_db,
                "UserName": self.username,
                "Password": self.password
            }
            
            response = requests.post(
                login_url,
                json=payload,
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                self.session_id = response.cookies.get('B1SESSION')
                self.logger.info("✅ SAP B1 login successful")
                return True
            else:
                self.logger.error(f"❌ SAP B1 login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ SAP B1 login error: {e}")
            return False
    
    def logout(self):
        """Logout from SAP B1"""
        if not self.session_id:
            return
        
        try:
            logout_url = f"{self.server_url}/b1s/v1/Logout"
            requests.post(
                logout_url,
                cookies={'B1SESSION': self.session_id},
                verify=False,
                timeout=10
            )
            self.logger.info("✅ SAP B1 logout successful")
        except Exception as e:
            self.logger.warning(f"⚠️ SAP B1 logout error: {e}")
    
    def query_exists(self, sql_code):
        """Check if a SQL query exists in SAP B1"""
        try:
            url = f"{self.server_url}/b1s/v1/SQLQueries('{sql_code}')"
            response = requests.get(
                url,
                cookies={'B1SESSION': self.session_id},
                verify=False,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"❌ Error checking query {sql_code}: {e}")
            return False
    
    def create_query(self, query_data):
        """Create a SQL query in SAP B1"""
        try:
            url = f"{self.server_url}/b1s/v1/SQLQueries"
            response = requests.post(
                url,
                json=query_data,
                cookies={'B1SESSION': self.session_id},
                verify=False,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"✅ Created SQL query: {query_data['SqlCode']}")
                return True
            else:
                self.logger.error(f"❌ Failed to create query {query_data['SqlCode']}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error creating query {query_data['SqlCode']}: {e}")
            return False
    
    def validate_and_create_queries(self):
        """Main method to validate all required queries and create missing ones"""
        self.logger.info("🔍 Starting SAP B1 SQL Query validation...")
        
        if not self.login():
            self.logger.warning("⚠️ Skipping SQL query validation - SAP B1 login failed")
            return False
        
        try:
            created_count = 0
            existing_count = 0
            failed_count = 0
            
            for query in self.required_queries:
                sql_code = query['SqlCode']
                
                if self.query_exists(sql_code):
                    self.logger.debug(f"✓ Query exists: {sql_code}")
                    existing_count += 1
                else:
                    self.logger.info(f"⚠️ Query missing: {sql_code} - Creating...")
                    if self.create_query(query):
                        created_count += 1
                    else:
                        failed_count += 1
            
            self.logger.info(f"📊 SQL Query validation complete:")
            self.logger.info(f"   - Existing: {existing_count}")
            self.logger.info(f"   - Created: {created_count}")
            self.logger.info(f"   - Failed: {failed_count}")
            
            return True
            
        finally:
            self.logout()


def validate_sap_queries(app, force=None):
    """Initialize and validate SAP B1 queries on app startup
    
    Args:
        app: Flask application instance
        force: If True, run validation even if it was already attempted
               If None, checks FORCE_SAP_VALIDATION environment variable
    """
    import os
    from datetime import datetime
    import hashlib
    
    flag_file = '.local/state/sap_queries_validated.flag'
    
    if force is None:
        force = os.environ.get('FORCE_SAP_VALIDATION', '').lower() in ('true', '1', 'yes')
    
    try:
        os.makedirs(os.path.dirname(flag_file), exist_ok=True)
        
        server = app.config.get('SAP_B1_SERVER')
        username = app.config.get('SAP_B1_USERNAME')
        password = app.config.get('SAP_B1_PASSWORD')
        company_db = app.config.get('SAP_B1_COMPANY_DB')
        
        current_db_hash = hashlib.md5(f"{company_db}".encode()).hexdigest()[:8] if company_db else "none"
        
        if not force and os.path.exists(flag_file):
            with open(flag_file, 'r') as f:
                flag_content = f.read()
            
            previous_db_hash = None
            for line in flag_content.split('\n'):
                if line.startswith('Database:'):
                    previous_db_hash = line.split(':', 1)[1].strip()
                    break
            
            if previous_db_hash and previous_db_hash != current_db_hash:
                logging.info("🔄 Database changed - re-running SQL query validation for new database")
            else:
                logging.info("✅ SQL query validation already attempted on initial startup - skipping")
                logging.info(f"💡 Flag file details: {flag_content.strip()}")
                logging.info("💡 To force re-validation, set FORCE_SAP_VALIDATION=true or delete: .local/state/sap_queries_validated.flag")
                return True
        
        if not all([server, username, password, company_db]):
            with open(flag_file, 'w') as f:
                f.write(f"Status: skipped - SAP B1 credentials not configured\n")
                f.write(f"Database: {current_db_hash}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            logging.warning("⚠️ SAP B1 credentials not configured - skipping SQL query validation")
            logging.info("✅ Flag file created - will skip on future restarts")
            return False
        
        logging.info("🔄 Running SQL query validation (initial startup attempt)...")
        manager = SAPQueryManager(server, username, password, company_db)
        result = manager.validate_and_create_queries()
        
        with open(flag_file, 'w') as f:
            if result:
                f.write(f"Status: completed successfully\n")
                f.write(f"Database: {current_db_hash}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                logging.info("✅ SQL query validation completed - flag file created, will skip on future restarts")
            else:
                f.write(f"Status: attempted but failed (SAP connection issue)\n")
                f.write(f"Database: {current_db_hash}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Note: Validation was attempted once. Will not retry on restarts unless database changes.\n")
                logging.warning("⚠️ SQL query validation failed (likely SAP connection unavailable)")
                logging.info("✅ Flag file created - will skip retry on future restarts to avoid repeated failures")
        
        return result
        
    except Exception as e:
        try:
            current_db_hash = hashlib.md5(f"{company_db}".encode()).hexdigest()[:8] if 'company_db' in locals() and company_db else "none"
            with open(flag_file, 'w') as f:
                f.write(f"Status: error during validation\n")
                f.write(f"Database: {current_db_hash}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Error: {str(e)}\n")
        except:
            pass
        logging.error(f"❌ Error during SAP query validation: {e}")
        logging.info("✅ Flag file created - will skip retry on future restarts")
        return False
