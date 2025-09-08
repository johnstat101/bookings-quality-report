from django.core.management.base import BaseCommand
from quality_monitor.models import Booking, TravelAgency, KQOffice, KQStaff
import random
from datetime import date, timedelta
from faker import Faker

class Command(BaseCommand):
    help = 'Generate 100 random sample bookings'

    def handle(self, *args, **options):
        fake = Faker()
        
        # Create sample offices
        offices = []
        for i in range(10):
            office, _ = KQOffice.objects.get_or_create(
                office_id=f'KQ{i+1:03d}',
                defaults={
                    'name': f'KQ Office {fake.city()}',
                    'location': fake.city(),
                    'manager': fake.name()
                }
            )
            offices.append(office)
        
        # Create sample staff
        staff_members = []
        for i in range(20):
            staff, _ = KQStaff.objects.get_or_create(
                staff_id=f'ST{i+1:03d}',
                defaults={
                    'name': fake.name(),
                    'office': random.choice(offices),
                    'email': fake.email()
                }
            )
            staff_members.append(staff)
        
        # Create sample agencies
        agencies = []
        for i in range(5):
            agency, _ = TravelAgency.objects.get_or_create(
                iata_code=f'AG{i+1:02d}',
                defaults={
                    'name': f'{fake.company()} Travel',
                    'contact_email': fake.email(),
                    'contact_phone': fake.phone_number()[:20]
                }
            )
            agencies.append(agency)
        
        # Create specific offices for single-channel operations
        website_office, _ = KQOffice.objects.get_or_create(
            office_id='WEB001',
            defaults={
                'name': 'Website Office',
                'location': 'Online',
                'manager': 'Digital Manager'
            }
        )
        
        mobile_office, _ = KQOffice.objects.get_or_create(
            office_id='MOB001',
            defaults={
                'name': 'Mobile App Office',
                'location': 'Mobile Platform',
                'manager': 'Mobile Manager'
            }
        )
        
        call_center_office, _ = KQOffice.objects.get_or_create(
            office_id='CC001',
            defaults={
                'name': 'Call Center',
                'location': 'Nairobi',
                'manager': 'Call Center Manager'
            }
        )
        
        # Generate 100 bookings
        channels = [choice[0] for choice in Booking.CHANNEL_CHOICES]
        
        for i in range(100):
            channel = random.choice(channels)
            
            # Assign office/staff/agency based on specific channel requirements
            office = None
            staff = None
            agency = None
            
            if channel == 'website':
                # Website channel only uses website office
                office = website_office
            elif channel == 'mobile':
                # Mobile channel only uses mobile office
                office = mobile_office
            elif channel == 'cec':
                # CEC channel only uses call center office
                office = call_center_office
            elif channel in ['ato', 'cto', 'kq_gsa']:
                # These channels use physical offices
                office = random.choice(offices)
            elif channel == 'travel_agents':
                # Travel agents use agencies
                agency = random.choice(agencies)
                staff = random.choice(staff_members)
            elif channel in ['ndc', 'msafiri_connect']:
                # These channels use staff members
                staff = random.choice(staff_members)
            
            Booking.objects.create(
                pnr=f'KQ{fake.random_number(digits=6)}',
                phone=fake.phone_number()[:20] if random.random() > 0.3 else '',
                email=fake.email() if random.random() > 0.2 else '',
                ff_number=f'KQ{fake.random_number(digits=8)}' if random.random() > 0.6 else '',
                meal_selection=random.choice(['VGML', 'KSML', 'MOML', '']) if random.random() > 0.5 else '',
                seat=f'{random.randint(1,30)}{random.choice("ABCDEF")}' if random.random() > 0.4 else '',
                channel=channel,
                departure_date=fake.date_between(start_date='today', end_date='+30d'),
                kq_office=office,
                kq_staff=staff,
                travel_agency=agency
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully created 100 sample bookings'))