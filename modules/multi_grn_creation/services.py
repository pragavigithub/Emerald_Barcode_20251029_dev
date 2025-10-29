"""
SAP B1 Service Layer integration for Multiple GRN Creation
Provides methods to interact with SAP B1 APIs for customer, PO, and GRN creation
"""
import logging
import requests
import json
from datetime import datetime
import os
from flask import current_app
import urllib.parse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SAPMultiGRNService:
    """Service class for SAP B1 integration specific to Multiple GRN Creation"""
    
    def __init__(self):
        self.base_url = os.environ.get('SAP_B1_SERVER', '')
        self.username = os.environ.get('SAP_B1_USERNAME', '')
        self.password = os.environ.get('SAP_B1_PASSWORD', '')
        self.company_db = os.environ.get('SAP_B1_COMPANY_DB', '')
        self.session_id = None
        self.session = requests.Session()
        self.session.verify = False  # For development, in production use proper SSL
        self.is_offline = False
        self.enable_mock_data = os.environ.get('ENABLE_MOCK_SAP_DATA', 'false').lower() == 'true'

        

    
    def login(self):
        """Login to SAP B1 Service Layer"""
        if not all([self.base_url, self.username, self.password, self.company_db]):
            logging.warning("⚠️ SAP B1 configuration incomplete. Please check environment variables.")
            logging.warning(f"   SAP_B1_SERVER: {'✓' if self.base_url else '✗'}")
            logging.warning(f"   SAP_B1_USERNAME: {'✓' if self.username else '✗'}")
            logging.warning(f"   SAP_B1_PASSWORD: {'✓' if self.password else '✗'}")
            logging.warning(f"   SAP_B1_COMPANY_DB: {'✓' if self.company_db else '✗'}")
            return False
        
        login_url = f"{self.base_url}/b1s/v1/Login"
        login_data = {
            "UserName": self.username,
            "Password": self.password,
            "CompanyDB": self.company_db
        }
        
        try:
            logging.info(f"🔐 Attempting SAP login to {self.base_url}...")
            response = self.session.post(login_url, json=login_data, timeout=30)
            if response.status_code == 200:
                self.session_id = response.json().get('SessionId')
                logging.info("✅ SAP B1 login successful"+self.session_id)
                logging.info("✅ SAP B1 login successful")
                return True
            else:
                logging.warning(f"❌ SAP B1 login failed (Status {response.status_code}): {response.text}")
                logging.error(f"❌ SAP B1 login failed (Status {response.status_code}): {response.text}")
                return False
        except requests.exceptions.ConnectionError as e:
            logging.error(f"❌ SAP B1 connection failed: Cannot reach {self.base_url}")
            logging.error(f"❌ SAP B1 connection failed: Cannot reach {self.base_url}")
            logging.error(f"   This may be a network issue or the SAP server may not be accessible from Replit")
            logging.error(f"   Error details: {str(e)}")
            return False
        except requests.exceptions.Timeout:
            logging.error(f"❌ SAP B1 login timeout: Server did not respond within 30 seconds")
            return False
        except Exception as e:
            logging.error(f"❌ SAP B1 login error: {str(e)}")
            return False
    
    def ensure_logged_in(self):
        """Ensure we have a valid session, login if needed"""
        if not self.session_id:
            return self.login()
        return True
    
    def fetch_business_partners(self, card_type='S'):
        """
        Fetch valid Business Partners (Suppliers/Customers)
        card_type: 'S' for Suppliers, 'C' for Customers
        """
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            filter_query = f"Valid eq 'tYES' and CardType eq '{card_type}'"
            url = f"{self.base_url}/b1s/v1/BusinessPartners"
            params = {
                '$filter': filter_query,
                '$select': 'CardCode,CardName,Valid,CardType'
            }
            headers = {'Prefer': 'odata.maxpagesize=0'}
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                partners = data.get('value', [])
                logging.info(f"✅ Fetched {len(partners)} business partners")
                return {'success': True, 'partners': partners}
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.fetch_business_partners(card_type)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                logging.error(f"❌ Failed to fetch business partners: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logging.error(f"❌ Error fetching business partners: {str(e)}")
            return {'success': False, 'error': str(e)}

    def fetch_all_valid_customers(self):
            """Fetch all valid Business Partners for dropdown display"""
            if self.enable_mock_data:
                logging.info("📋 Using mock customer data (ENABLE_MOCK_SAP_DATA=true)")
                return self.get_mock_customers()
            
            if not self.ensure_logged_in():
                error_msg = 'SAP login failed - using mock data as fallback'
                logging.warning(f"⚠️ {error_msg}")
                return self.get_mock_customers()

            try:
                url = f"{self.base_url}/b1s/v1/BusinessPartners"
                params = {
                    '$filter': f"Valid eq 'tYES'",
                    '$select': 'CardCode,CardName,Valid'
                }
                headers = {'Prefer': 'odata.maxpagesize=0'}

                logging.info(f"📡 Fetching BusinessPartners from SAP: {url}")
                response = self.session.get(url, params=params, headers=headers, timeout=30)

                logging.info(f"📊 SAP Response Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    customers = [
                        {
                            'CardCode': c['CardCode'],
                            'CardName': c['CardName']
                        }
                        for c in data.get('value', [])
                        if c.get('Valid') == 'tYES'
                    ]
                    logging.info(f"✅ Successfully loaded {len(customers)} valid customers from SAP")
                    return {'success': True, 'customers': customers}

                elif response.status_code == 401:
                    self.session_id = None
                    logging.warning("⚠️ Session expired, attempting re-login...")
                    if self.login():
                        return self.fetch_all_valid_customers()
                    return {'success': False, 'error': 'SAP authentication failed - invalid credentials'}

                else:
                    error_msg = f"SAP API error (Status {response.status_code}): {response.text}"
                    logging.error(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg}

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Cannot connect to SAP server at {self.base_url} - using mock data as fallback"
                logging.warning(f"⚠️ {error_msg}")
                return self.get_mock_customers()
            except requests.exceptions.Timeout:
                error_msg = "SAP request timeout - using mock data as fallback"
                logging.warning(f"⚠️ {error_msg}")
                return self.get_mock_customers()
            except Exception as e:
                error_msg = f"Unexpected error fetching customers - using mock data as fallback: {str(e)}"
                logging.warning(f"⚠️ {error_msg}")
                return self.get_mock_customers()


    
    def fetch_open_purchase_orders_by_name(self, card_name):
        """
        Fetch open Purchase Orders for a specific customer/supplier by CardName
        Returns only POs with DocumentStatus = 'bost_Open' and open line items
        """
        if self.enable_mock_data:
            logging.info(f"📋 Using mock PO data for {card_name} (ENABLE_MOCK_SAP_DATA=true)")
            return self.get_mock_purchase_orders(card_name)
        
        if not self.ensure_logged_in():
            logging.warning(f"⚠️ SAP login failed - using mock PO data for {card_name}")
            return self.get_mock_purchase_orders(card_name)
        try:
            url = f"{self.base_url}/b1s/v1/PurchaseOrders"
            params = {
                '$filter': f"CardName eq '{card_name}' and DocumentStatus eq 'bost_Open'",
                '$select': 'DocEntry,DocNum,CardCode,CardName,DocDate,DocDueDate,DocTotal,DocumentStatus,DocumentLines'
            }
            
            logging.info(f"🔍 Fetching open POs for CardName: {card_name}")
            logging.info(f"  SAP URL: {url}?$filter={params['$filter']}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                pos = data.get('value', [])
                open_pos = []
                for po in pos:
                    open_lines = [
                        line for line in po.get('DocumentLines')
                        if line.get('LineStatus') == 'bost_Open' and line.get('Quantity', 0) > 0
                    ]
                    if open_lines:
                        po['OpenLines'] = open_lines
                        po['TotalOpenLines'] = len(open_lines)
                        open_pos.append(po)

                logging.info(f"✅ Fetched {len(open_pos)} open POs for CardName {card_name}")
                return {'success': True, 'purchase_orders': open_pos}
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.fetch_open_purchase_orders_by_name(card_name)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                logging.warning(f"⚠️ Failed to fetch POs for CardName {card_name} - using mock data: {response.text}")
                return self.get_mock_purchase_orders(card_name)
                
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"⚠️ Cannot connect to SAP - using mock PO data for {card_name}")
            return self.get_mock_purchase_orders(card_name)
        except requests.exceptions.Timeout:
            logging.warning(f"⚠️ SAP request timeout - using mock PO data for {card_name}")
            return self.get_mock_purchase_orders(card_name)
        except Exception as e:
            logging.warning(f"⚠️ Error fetching POs for {card_name} - using mock data: {str(e)}")
            return self.get_mock_purchase_orders(card_name)
    

    
    def create_purchase_delivery_note(self, grn_data):

        
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed - GRN not created'}
        
        try:
            url = f"{self.base_url}/b1s/v1/PurchaseDeliveryNotes"
            print(grn_data)
            response = self.session.post(url, json=grn_data, timeout=60)
            
            if response.status_code == 201:
                result = response.json()
                doc_entry = result.get('DocEntry')
                doc_num = result.get('DocNum')
                logging.info(f"✅ GRN created successfully: DocNum={doc_num}, DocEntry={doc_entry}")
                return {
                    'success': True,
                    'doc_entry': doc_entry,
                    'doc_num': doc_num,
                    'response': result
                }
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.create_purchase_delivery_note(grn_data)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                error_msg = response.text
                logging.error(f"❌ Failed to create GRN: {error_msg}")
                return {'success': False, 'error': error_msg, 'status_code': response.status_code}

        except Exception as e:
            logging.error(f"❌ Error creating GRN: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_mock_customers(self):
        """Generate mock customer data for testing without SAP connectivity"""
        return {
            'success': True,
            'customers': [

            ]
        }
    
    def validate_item_code(self, item_code):
        """
        Validate item code and get batch/serial management info
        Uses SAP B1 SQLQueries endpoint to check item properties
        """
        if not self.ensure_logged_in():
            logging.warning(f"⚠️ SAP login failed - cannot validate item {item_code}")
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            url = f"{self.base_url}/b1s/v1/SQLQueries('ItemCode_Batch_Serial_Val')/List"
            payload = {
                "ParamList": f"itemCode='{item_code}'"
            }
            
            logging.info(f"🔍 Validating item code: {item_code}")
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('value', [])
                
                if not items:
                    logging.warning(f"⚠️ Item code {item_code} not found in SAP")
                    return {'success': False, 'error': f'Item code {item_code} not found'}
                
                item_data = items[0]
                batch_managed = item_data.get('BatchNum', 'N') == 'Y'
                serial_managed = item_data.get('SerialNum', 'N') == 'Y'
                management_method = item_data.get('NonBatch_NonSerialMethod', 'N')
                
                # Determine inventory type
                if serial_managed:
                    inventory_type = 'serial'
                elif batch_managed:
                    inventory_type = 'batch'
                elif management_method == 'R':
                    inventory_type = 'quantity_based'
                else:
                    inventory_type = 'standard'
                
                logging.info(f"✅ Item {item_code} validated: Type={inventory_type}")
                return {
                    'success': True,
                    'item_code': item_data.get('ItemCode'),
                    'batch_managed': batch_managed,
                    'serial_managed': serial_managed,
                    'inventory_type': inventory_type,
                    'management_method': management_method,
                    'item_data': item_data
                }
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.validate_item_code(item_code)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                error_msg = response.text
                logging.error(f"❌ Failed to validate item {item_code}: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            logging.error(f"❌ Error validating item {item_code}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_item_details(self, item_code):
        """
        Fetch item details from SAP B1
        Returns item name, UoM, price, and other details
        """
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            url = f"{self.base_url}/b1s/v1/Items('{item_code}')"
            params = {
                '$select': 'ItemCode,ItemName,InventoryUOM,PurchaseUnit,SalesUnit,QuantityOnStock'
            }
            
            logging.info(f"📦 Fetching item details for: {item_code}")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                item_data = response.json()
                logging.info(f"✅ Item details fetched for {item_code}")
                return {
                    'success': True,
                    'item': item_data
                }
            elif response.status_code == 404:
                return {'success': False, 'error': f'Item {item_code} not found'}
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.get_item_details(item_code)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logging.error(f"❌ Error fetching item details: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_mock_purchase_orders(self, card_code):
        """Generate mock purchase orders for testing without SAP connectivity"""
        return {

        }
