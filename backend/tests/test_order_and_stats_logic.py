from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.statistics.models import SellerRating
from apps.textbooks.models import Textbook
from apps.users.models import User


class OrderAndStatsLogicTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="Passw0rd!",
            role="student",
        )

    def _create_textbook(self, owner, title="测试教材", status="approved", transaction_type="sell"):
        textbook = Textbook.objects.create(
            title=title,
            author="测试作者",
            price=Decimal("20.00"),
            owner=owner,
            status=status,
            transaction_type=transaction_type,
        )
        # Some review signals may override status on create; enforce test target status.
        Textbook.objects.filter(pk=textbook.pk).update(status=status)
        textbook.refresh_from_db()
        return textbook

    def test_order_create_marks_textbook_unavailable_for_next_buyer(self):
        seller = self._create_user("seller_a")
        buyer1 = self._create_user("buyer_a")
        buyer2 = self._create_user("buyer_b")
        textbook = self._create_textbook(owner=seller, status="approved", transaction_type="sell")

        self.client.force_authenticate(user=buyer1)
        first = self.client.post("/api/orders/create/", {"textbook_id": textbook.id}, format="json")
        self.assertEqual(first.status_code, 201)

        textbook.refresh_from_db()
        self.assertEqual(textbook.status, "sold")

        self.client.force_authenticate(user=buyer2)
        second = self.client.post("/api/orders/create/", {"textbook_id": textbook.id}, format="json")
        self.assertEqual(second.status_code, 404)

    def test_cancel_keeps_textbook_unavailable_if_another_active_order_exists(self):
        seller = self._create_user("seller_b")
        buyer1 = self._create_user("buyer_c")
        buyer2 = self._create_user("buyer_d")
        textbook = self._create_textbook(owner=seller, status="sold", transaction_type="sell")

        order1 = Order.objects.create(
            textbook=textbook,
            buyer=buyer1,
            seller=seller,
            transaction_type="sell",
            price=Decimal("20.00"),
            status="pending",
        )
        Order.objects.create(
            textbook=textbook,
            buyer=buyer2,
            seller=seller,
            transaction_type="sell",
            price=Decimal("20.00"),
            status="pending",
        )

        self.client.force_authenticate(user=buyer1)
        resp = self.client.post(
            f"/api/orders/{order1.id}/cancel/",
            {"reason": "duplicate"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

        textbook.refresh_from_db()
        self.assertEqual(textbook.status, "sold")

    def test_user_funnel_counts_include_non_approved_owned_textbooks(self):
        seller = self._create_user("seller_c")
        buyer = self._create_user("buyer_e")

        self._create_textbook(owner=seller, title="在架教材", status="approved")
        sold_tb = self._create_textbook(owner=seller, title="已售教材", status="sold")

        Order.objects.create(
            textbook=sold_tb,
            buyer=buyer,
            seller=seller,
            transaction_type="sell",
            price=Decimal("20.00"),
            status="completed",
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )

        self.client.force_authenticate(user=seller)
        resp = self.client.get("/api/statistics/user-insights/?limit=10")
        self.assertEqual(resp.status_code, 200)

        funnel = resp.data.get("textbook_funnel", {})
        self.assertEqual(funnel.get("listed"), 1)
        self.assertEqual(funnel.get("ordered"), 1)
        self.assertEqual(funnel.get("completed"), 1)

    def test_seller_rating_can_be_updated_by_same_user(self):
        seller = self._create_user("seller_rating_a")
        buyer = self._create_user("buyer_rating_a")
        textbook = self._create_textbook(owner=seller, status="approved", transaction_type="sell")

        Order.objects.create(
            textbook=textbook,
            buyer=buyer,
            seller=seller,
            transaction_type="sell",
            price=Decimal("20.00"),
            status="completed",
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )

        self.client.force_authenticate(user=buyer)
        first = self.client.post(
            "/api/statistics/seller-ratings/create/",
            {"seller_id": seller.id, "score": "4.0", "comment": "初评"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            "/api/statistics/seller-ratings/create/",
            {"seller_id": seller.id, "score": "5.0", "comment": "改评"},
            format="json",
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(SellerRating.objects.filter(seller=seller, rater=buyer).count(), 1)
        self.assertEqual(float(SellerRating.objects.get(seller=seller, rater=buyer).score), 5.0)

    def test_textbook_rating_can_update_and_cancel(self):
        seller = self._create_user("seller_rating_b")
        buyer = self._create_user("buyer_rating_b")
        textbook = self._create_textbook(owner=seller, status="approved", transaction_type="sell")

        self.client.force_authenticate(user=buyer)
        create_resp = self.client.post(
            f"/api/textbooks/{textbook.id}/rating/",
            {"score": 4},
            format="json",
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertEqual(create_resp.data.get("action"), "created")

        update_resp = self.client.post(
            f"/api/textbooks/{textbook.id}/rating/",
            {"score": 5},
            format="json",
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.data.get("action"), "updated")

        cancel_resp = self.client.post(
            f"/api/textbooks/{textbook.id}/rating/",
            {"score": 0},
            format="json",
        )
        self.assertEqual(cancel_resp.status_code, 200)
        self.assertEqual(cancel_resp.data.get("action"), "cancelled")
        self.assertEqual(cancel_resp.data.get("rating_count"), 0)
