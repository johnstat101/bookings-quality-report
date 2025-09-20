from django.test import TestCase, Client
from django.urls import reverse
from .models import PNR, Contact, Passenger
from datetime import date
import json

class PNRModelTest(TestCase):
    def setUp(self):
        self.pnr = PNR.objects.create(
            control_number='TEST123',
            office_id='NBO001',
            creation_date=date.today()
        )
    
    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        # Add valid contact
        Contact.objects.create(
            pnr=self.pnr,
            contact_type='APE',
            contact_detail='test@example.com'
        )
        
        # Add passenger with FF number
        Passenger.objects.create(
            pnr=self.pnr,
            surname='Test',
            first_name='User',
            ff_number='KQ12345678'
        )
        
        # Quality score should be 60 (40 for contact + 20 for FF)
        self.assertEqual(self.pnr.quality_score, 60)
    
    def test_contact_validation(self):
        """Test contact validation logic"""
        # Valid email
        email_contact = Contact.objects.create(
            pnr=self.pnr,
            contact_type='APE',
            contact_detail='test@example.com'
        )
        self.assertTrue(email_contact.is_valid_email)
        
        # Invalid email in wrong field
        phone_contact = Contact.objects.create(
            pnr=self.pnr,
            contact_type='APM',
            contact_detail='test@example.com'
        )
        self.assertTrue(phone_contact.is_wrongly_placed)

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.pnr = PNR.objects.create(
            control_number='TEST123',
            office_id='NBO001',
            creation_date=date.today()
        )
    
    def test_home_view_loads(self):
        """Test that home view loads successfully"""
        response = self.client.get(reverse('quality_monitor:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total PNRs')
    
    def test_filtering_works(self):
        """Test that filtering functionality works"""
        response = self.client.get(reverse('quality_monitor:home'), {
            'offices': ['NBO001'],
            'start_date': '2024-01-01'
        })
        self.assertEqual(response.status_code, 200)

class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.pnr = PNR.objects.create(
            control_number='TEST123',
            office_id='NBO001',
            delivery_system_company='KQ'
        )
    
    def test_delivery_systems_api(self):
        """Test delivery systems API endpoint"""
        response = self.client.get(reverse('quality_monitor:api_delivery_systems'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('delivery_systems', data)
