"""
Azure Document Intelligence Service
Handles receipt scanning and extraction
"""

import requests
import time
from datetime import datetime
from config import Config

class AzureService:
    """Service for Azure Document Intelligence"""
    
    def __init__(self):
        self.endpoint = Config.AZURE_ENDPOINT
        self.key = Config.AZURE_KEY
    
    def analyze_receipt(self, image_path: str) -> dict:
        """Analyze receipt with Azure Document Intelligence"""
        if not self.endpoint or not self.key:
            # Return mock data for testing
            return self._mock_response()
        
        analyze_url = f"{self.endpoint}/formrecognizer/documentModels/prebuilt-receipt:analyze?api-version=2023-07-31"
        headers = {
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': self.key
        }
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            response = requests.post(analyze_url, headers=headers, data=image_data)
            
            if response.status_code != 202:
                return {'success': False, 'error': f'Failed: {response.text}'}
            
            operation_url = response.headers.get('Operation-Location')
            
            # Poll for results
            for _ in range(30):
                time.sleep(1)
                result = requests.get(
                    operation_url,
                    headers={'Ocp-Apim-Subscription-Key': self.key}
                ).json()
                
                if result.get('status') == 'succeeded':
                    return self._parse_response(result)
                elif result.get('status') == 'failed':
                    return {'success': False, 'error': 'Analysis failed'}
            
            return {'success': False, 'error': 'Timeout'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _parse_response(self, result: dict) -> dict:
        """Parse Azure response"""
        items = []
        store = 'Unknown'
        date = None
        total = 0.0
        
        try:
            docs = result.get('analyzeResult', {}).get('documents', [])
            if docs:
                fields = docs[0].get('fields', {})
                
                if 'MerchantName' in fields:
                    store = fields['MerchantName'].get('valueString', 'Unknown')
                
                if 'TransactionDate' in fields:
                    date = fields['TransactionDate'].get('valueDate')
                
                if 'Items' in fields:
                    for item in fields['Items'].get('valueArray', []):
                        f = item.get('valueObject', {})
                        name = f.get('Description', {}).get('valueString', 'Unknown')
                        price = f.get('TotalPrice', {}).get('valueCurrency', {}).get('amount', 0)
                        items.append({
                            'name': name,
                            'price': float(price),
                            'category': self._categorize_item(name)
                        })
                
                if 'Total' in fields:
                    total = fields['Total'].get('valueCurrency', {}).get('amount', 0)
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'store': store,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'items': items,
            'total': float(total)
        }
    
    def _categorize_item(self, item_name: str) -> str:
        """Categorize item based on name"""
        item_lower = item_name.lower()
        mappings = {
            'Groceries': ['milk', 'bread', 'cheese', 'meat', 'vegetable', 'fruit', 'grocery', 'food'],
            'Car': ['gas', 'fuel', 'parking', 'toll', 'car wash', 'oil change', 'tire'],
            'Entertainment': ['movie', 'game', 'concert', 'ticket', 'bowling'],
            'Subscriptions': ['netflix', 'spotify', 'hulu', 'disney', 'amazon prime', 'subscription'],
            'Electric': ['electric', 'power', 'utility'],
            'Medical': ['medicine', 'pharmacy', 'doctor', 'medical', 'health', 'hospital'],
            'Household': ['cleaning', 'paper towel', 'toilet paper', 'detergent', 'home'],
            'Eating Out': ['restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'takeout'],
            'Shopping': ['clothes', 'shoes', 'amazon', 'target', 'clothing'],
            'Rent': ['rent', 'lease'],
            'Investment': ['stock', 'etf', 'investment', '401k'],
        }
        
        for category, keywords in mappings.items():
            if any(kw in item_lower for kw in keywords):
                return category
        
        return 'Other'
    
    def _mock_response(self) -> dict:
        """Mock response for testing without Azure"""
        return {
            'success': True,
            'store': 'Sample Store',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'items': [
                {'name': 'Sample Item 1', 'price': 9.99, 'category': 'Groceries'},
                {'name': 'Sample Item 2', 'price': 14.99, 'category': 'Groceries'},
            ],
            'total': 24.98
        }

# Singleton instance
azure_service = AzureService()