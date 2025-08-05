from django.test import TestCase
from django.contrib.auth import get_user_model
from system.models import SystemPlan
from .models import Gym

User = get_user_model()

class GymModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', role='gym_owner')
        self.plan = SystemPlan.objects.create(
            name='Test Plan',
            plan_type='basic',
            price=100,
            duration_days=30,
            gym_limit=1,
            member_limit=100
        )

    def test_create_gym(self):
        gym = Gym.objects.create(
            owner=self.user,
            name='Test Gym',
            address='123 Test St',
            phone='1234567890',
            email='test@example.com',
            system_plan=self.plan
        )
        self.assertEqual(gym.name, 'Test Gym')
        self.assertEqual(gym.owner, self.user)
        self.assertEqual(gym.system_plan, self.plan)
        self.assertFalse(gym.is_active)
        self.assertFalse(gym.is_approved)
        self.assertIsNotNone(gym.expiry_date)

from .models import Member, GymPlan
from django.core.signing import Signer

class MemberModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', role='gym_owner')
        self.plan = SystemPlan.objects.create(
            name='Test Plan',
            plan_type='basic',
            price=100,
            duration_days=30,
            gym_limit=1,
            member_limit=100
        )
        self.gym = Gym.objects.create(
            owner=self.user,
            name='Test Gym',
            address='123 Test St',
            phone='1234567890',
            email='test@example.com',
            system_plan=self.plan
        )
        self.gym_plan = GymPlan.objects.create(
            gym=self.gym,
            name='Test Gym Plan',
            plan_type='individual_duration',
            price=50,
            duration_days=30
        )

    def test_create_member_and_qr_code(self):
        member = Member.objects.create(
            gym=self.gym,
            name='Test Member',
            phone='1234567890',
            gender='male',
            member_type='individual',
            plan=self.gym_plan
        )
        self.assertIsNotNone(member.qr_code)

        # For now, we just check that the qr_code is not empty.
        # A more advanced test would read the QR code and verify its content.
        self.assertTrue(member.qr_code)
