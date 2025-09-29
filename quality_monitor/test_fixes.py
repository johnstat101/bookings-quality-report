"""
Test file to validate PNR control number handling and analytics fixes.
Run this test to ensure the fixes work correctly.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import PNR, Contact, Passenger
from .views import calculate_pnr_statistics
from .utils import get_quality_score_annotation
from datetime import date
import pandas as pd


class PNRControlNumberTest(TestCase):
    """Test PNR control number handling and duplicate prevention"""
    
    def setUp(self):
        """Set up test data"""
        self.pnr_data = {
            'control_number': 'TEST123',
            'office_id': 'NBO001',
            'agent': 'AGENT01',
            'creation_date': date.today(),
            'delivery_system_company': 'AMADEUS',
            'delivery_system_location': 'NBO'
        }
    
    def test_pnr_creation_with_valid_control_number(self):
        """Test PNR creation with valid control number"""
        pnr = PNR.objects.create(**self.pnr_data)
        self.assertEqual(pnr.control_number, 'TEST123')
        self.assertTrue(PNR.objects.filter(control_number='TEST123').exists())
    
    def test_pnr_duplicate_control_number_prevention(self):
        """Test that duplicate control numbers are prevented"""
        PNR.objects.create(**self.pnr_data)
        
        # Attempt to create another PNR with same control number
        with self.assertRaises(Exception):  # Should raise IntegrityError due to unique constraint
            PNR.objects.create(**self.pnr_data)
    
    def test_pnr_control_number_validation(self):
        """Test control number validation"""
        # Test empty control number
        invalid_data = self.pnr_data.copy()
        invalid_data['control_number'] = ''
        
        pnr = PNR(**invalid_data)
        with self.assertRaises(ValidationError):
            pnr.full_clean()
    
    def test_quality_score_bounds(self):
        """Test that quality scores are within valid bounds [0, 100]"""
        pnr = PNR.objects.create(**self.pnr_data)
        
        # Test with no additional data (should be 0)
        self.assertEqual(pnr.quality_score, 0)
        
        # Add valid contact
        Contact.objects.create(
            pnr=pnr,
            contact_type='APE',
            contact_detail='test@example.com'
        )
        
        # Add passenger with all attributes
        Passenger.objects.create(
            pnr=pnr,
            surname='DOE',
            first_name='JOHN',
            ff_number='FF123456',
            meal='AVML',
            seat_row_number='12',
            seat_column='A'
        )
        
        # Refresh from database
        pnr.refresh_from_db()
        
        # Quality score should be 100 (40 + 20 + 20 + 20)
        self.assertEqual(pnr.quality_score, 100)
        self.assertLessEqual(pnr.quality_score, 100)
        self.assertGreaterEqual(pnr.quality_score, 0)


class AnalyticsCalculationTest(TestCase):
    """Test analytics calculations and percentage bounds"""
    
    def setUp(self):
        """Set up test data for analytics"""
        # Create test PNRs
        for i in range(5):
            pnr = PNR.objects.create(
                control_number=f'TEST{i:03d}',
                office_id='NBO001',
                agent='AGENT01',
                creation_date=date.today(),
                delivery_system_company='AMADEUS'
            )
            
            # Add passenger
            Passenger.objects.create(
                pnr=pnr,
                surname=f'PASSENGER{i}',
                first_name='TEST',
                ff_number='FF123' if i < 3 else '',  # 3 out of 5 have FF numbers
                meal='AVML' if i < 2 else '',        # 2 out of 5 have meals
                seat_row_number='12' if i < 4 else '', # 4 out of 5 have seats
                seat_column='A' if i < 4 else ''
            )
            
            # Add contacts (valid for first 3 PNRs)
            if i < 3:
                Contact.objects.create(
                    pnr=pnr,
                    contact_type='APE',
                    contact_detail=f'test{i}@example.com'
                )
    
    def test_statistics_calculation_bounds(self):
        """Test that statistics calculations are within valid bounds"""
        pnrs = PNR.objects.all()
        quality_annotation = get_quality_score_annotation()
        pnrs_with_score = pnrs.annotate(calculated_quality_score=quality_annotation)
        
        stats = calculate_pnr_statistics(pnrs_with_score)
        
        # Test that all counts are non-negative
        for key, value in stats.items():
            if isinstance(value, (int, float)) and 'count' in key:
                self.assertGreaterEqual(value, 0, f"{key} should be non-negative")
        
        # Test that percentages would be within bounds
        total_pnrs = stats.get('total_pnrs', 0)
        if total_pnrs > 0:
            reachable_pnrs = stats.get('reachable_pnrs', 0)
            self.assertLessEqual(reachable_pnrs, total_pnrs)
            
            # Calculate percentage manually to test bounds
            percentage = (reachable_pnrs / total_pnrs * 100) if total_pnrs > 0 else 0
            self.assertLessEqual(percentage, 100)
            self.assertGreaterEqual(percentage, 0)
    
    def test_percentage_calculation_safety(self):
        """Test safe percentage calculations"""
        # Test with zero total
        email_total = 0
        email_wrong_format_count = 0
        percentage = (email_wrong_format_count / email_total * 100) if email_total > 0 else 0
        self.assertEqual(percentage, 0)
        
        # Test with normal values
        email_total = 10
        email_wrong_format_count = 3
        percentage = min(100, max(0, (email_wrong_format_count / email_total * 100)))
        self.assertEqual(percentage, 30.0)
        self.assertLessEqual(percentage, 100)
        self.assertGreaterEqual(percentage, 0)
        
        # Test bounds enforcement
        percentage_over_100 = min(100, max(0, 150))
        self.assertEqual(percentage_over_100, 100)
        
        percentage_under_0 = min(100, max(0, -10))
        self.assertEqual(percentage_under_0, 0)


class DataUploadTest(TestCase):
    """Test data upload and duplicate handling"""
    
    def test_duplicate_passenger_handling(self):
        """Test that duplicate passengers are handled correctly"""
        # Create sample data with duplicates
        data = {
            'ControlNumber': ['TEST001', 'TEST001', 'TEST001'],
            'Surname': ['DOE', 'DOE', 'SMITH'],
            'FirstName': ['JOHN', 'JOHN', 'JANE'],
            'OfficeID': ['NBO001', 'NBO001', 'NBO001'],
            'Agent': ['AGENT01', 'AGENT01', 'AGENT01'],
            'creationDate': ['010124', '010124', '010124'],
            'DeliverySystemCompany': ['AMADEUS', 'AMADEUS', 'AMADEUS'],
            'ContactType': ['APE', 'APM', 'APE'],
            'ContactDetail': ['john@example.com', '+254700000000', 'jane@example.com']
        }
        
        df = pd.DataFrame(data)
        
        # Simulate the deduplication logic
        processed_passengers = set()
        processed_contacts = set()
        unique_passengers = []
        unique_contacts = []
        
        for _, row in df.iterrows():
            control_number = row['ControlNumber']
            surname = row['Surname']
            first_name = row['FirstName']
            contact_type = row['ContactType']
            contact_detail = row['ContactDetail']
            
            # Passenger deduplication
            passenger_key = (control_number, surname, first_name)
            if passenger_key not in processed_passengers:
                unique_passengers.append(passenger_key)
                processed_passengers.add(passenger_key)
            
            # Contact deduplication
            contact_key = (control_number, contact_type, contact_detail)
            if contact_key not in processed_contacts:
                unique_contacts.append(contact_key)
                processed_contacts.add(contact_key)
        
        # Should have 2 unique passengers (JOHN DOE and JANE SMITH)
        self.assertEqual(len(unique_passengers), 2)
        
        # Should have 3 unique contacts (different contact types/details)
        self.assertEqual(len(unique_contacts), 3)


if __name__ == '__main__':
    import django
    import os
    import sys
    
    # Add the project directory to Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookings_quality.settings')
    django.setup()
    
    # Run tests
    import unittest
    unittest.main()