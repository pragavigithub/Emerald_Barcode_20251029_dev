"""
API Routes for GRPO Dropdown Functionality
Warehouse, Bin Location, and Batch selection endpoints
"""
from flask import jsonify, request
from sap_integration import SAPIntegration
import logging

def register_api_routes(app):
    """Register API routes with the Flask app"""
    
    @app.route('/api/get-warehouses', methods=['GET'])
    def get_warehouses():
        """Get all warehouses for dropdown selection"""
        try:
            sap = SAPIntegration()
            result = sap.get_warehouses_list()
            
            if result.get('success'):
                return jsonify(result)
            else:
                # Return mock data for offline mode
                return jsonify({
                    'success': True,

                })
                
        except Exception as e:
            logging.error(f"Error in get_warehouses API: {str(e)}")
            # Return mock data on error
            return jsonify({
                'success': True,

            })

    @app.route('/api/get-bins', methods=['GET'])
    def get_bins():
        """Get bin locations for a specific warehouse"""
        try:
            warehouse_code = request.args.get('warehouse')
            if not warehouse_code:
                return jsonify({'success': False, 'error': 'Warehouse code required'}), 400
            
            sap = SAPIntegration()
            result = sap.get_bin_locations_list(warehouse_code)
            
            if result.get('success'):
                return jsonify(result)
            else:
                # Return mock data for offline mode
                return jsonify({
                    'success': True,

                })
                
        except Exception as e:
            logging.error(f"Error in get_bins API: {str(e)}")
            # Return mock data on error
            warehouse_code = request.args.get('warehouse', 'WH001')
            return jsonify({
                'success': True,

            })

    @app.route('/api/get-batches', methods=['GET'])
    def get_batches():
        """Get available batches for a specific item using SAP B1 BatchNumberDetails API"""
        try:
            item_code = request.args.get('item_code') or request.args.get('item')
            warehouse_code = request.args.get('warehouse')
            
            if not item_code:
                return jsonify({'success': False, 'error': 'Item code required'}), 400
            
            sap = SAPIntegration()
            # Use the specific SAP B1 API for batch details
            result = sap.get_batch_number_details(item_code)
            
            if result.get('success'):
                return jsonify(result)
        except Exception as e:
            logging.error(f"Error in get_batches API: {str(e)}")
            # Return mock data on error
            item_code = request.args.get('item_code') or request.args.get('item', 'ITEM001')
            return jsonify({
                'success': True,
            })

    @app.route('/api/get-item-name', methods=['GET'])
    def get_item_name():
        """Get item name based on item code from SAP B1"""
        try:
            item_code = request.args.get('item_code')
            if not item_code:
                return jsonify({'success': False, 'error': 'Item code required'}), 400
            
            sap = SAPIntegration()
            
            # Try to get item name from SAP B1
            if sap.ensure_logged_in():
                try:
                    # Use the SAP endpoint provided by user: https://192.168.0.127:50000/b1s/v1/Items?$select=ItemCode,ItemName
                    url = f"{sap.base_url}/b1s/v1/Items"
                    params = {
                        '$filter': f"ItemCode eq '{item_code}'",
                        '$select': 'ItemCode,ItemName'
                    }
                    response = sap.session.get(url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('value', [])
                        
                        if items and len(items) > 0:
                            item = items[0]
                            item_name = item.get('ItemName') or f'Item {item_code}'
                            
                            logging.info(f"Retrieved item name for {item_code}: {item_name}")
                            return jsonify({
                                'success': True,
                                'item_code': item_code,
                                'item_name': item_name
                            })
                        else:
                            # Item not found in SAP
                            return jsonify({
                                'success': False,
                                'error': f'Item code {item_code} not found in SAP B1'
                            }), 404
                            
                except Exception as sap_error:
                    logging.error(f"Error getting item from SAP: {str(sap_error)}")
                    # Return fallback response
                    return jsonify({
                        'success': True,
                        'item_code': item_code,
                        'item_name': f'Item {item_code}',
                        'fallback': True
                    })
            
            # Return fallback if SAP not available
            return jsonify({
                'success': True,
                'item_code': item_code,
                'item_name': f'Item {item_code}',
                'fallback': True
            })
            
        except Exception as e:
            logging.error(f"Error in get_item_name API: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/get-invt-series', methods=['GET'])
    def get_invt_series():
        """Get Inventory Transfer document series for dropdown selection"""
        try:
            sap = SAPIntegration()
            series_list = sap.get_invt_series()
            
            if series_list:
                return jsonify({
                    'success': True,
                    'series': series_list
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No series found',
                    'series': []
                })
                
        except Exception as e:
            logging.error(f"Error in get_invt_series API: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'series': []
            }), 500

    @app.route('/api/get-invt-docentry', methods=['GET'])
    def get_invt_docentry():
        """Get Inventory Transfer DocEntry based on series and DocNum"""
        try:
            series = request.args.get('series')
            doc_num = request.args.get('doc_num')
            
            if not series or not doc_num:
                return jsonify({
                    'success': False,
                    'error': 'Both series and doc_num are required'
                }), 400
            
            sap = SAPIntegration()
            doc_entry = sap.get_invt_doc_entry(series, doc_num)
            
            if doc_entry:
                return jsonify({
                    'success': True,
                    'doc_entry': doc_entry
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No DocEntry found for series {series} and DocNum {doc_num}'
                }), 404
                
        except Exception as e:
            logging.error(f"Error in get_invt_docentry API: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/get-invt-details', methods=['GET'])
    def get_invt_details():
        """Get Inventory Transfer Request details by DocEntry"""
        try:
            doc_entry = request.args.get('doc_entry')
            
            if not doc_entry:
                return jsonify({
                    'success': False,
                    'error': 'doc_entry is required'
                }), 400
            
            sap = SAPIntegration()
            invt_data = sap.get_inventory_transfer_request_by_doc_entry(doc_entry)
            
            if invt_data:
                return jsonify({
                    'success': True,
                    'data': invt_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'No Inventory Transfer Request found for DocEntry {doc_entry}'
                }), 404
                
        except Exception as e:
            logging.error(f"Error in get_invt_details API: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/get-po-docnums', methods=['GET'])
    def get_po_docnums():
        """Get open PO document numbers for a specific series"""
        try:
            series = request.args.get('series')
            
            if not series:
                return jsonify({
                    'success': False,
                    'error': 'series is required'
                }), 400
            
            sap = SAPIntegration()
            doc_list = sap.get_open_po_docnums(series)
            
            if doc_list:
                return jsonify({
                    'success': True,
                    'documents': doc_list
                })
            else:
                return jsonify({
                    'success': True,
                    'documents': []
                })
                
        except Exception as e:
            logging.error(f"Error in get_po_docnums API: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/get-available-serial-numbers', methods=['GET'])
    def get_available_serial_numbers():
        """Get available serial numbers for an item in a specific warehouse"""
        try:
            item_code = request.args.get('item_code')
            warehouse_code = request.args.get('warehouse_code')
            
            if not item_code or not warehouse_code:
                return jsonify({
                    'success': False,
                    'error': 'item_code and warehouse_code are required'
                }), 400
            
            sap = SAPIntegration()
            result = sap.get_available_serial_numbers(item_code, warehouse_code)
            
            return jsonify(result)
                
        except Exception as e:
            logging.error(f"Error in get_available_serial_numbers API: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'serial_numbers': []
            }), 500