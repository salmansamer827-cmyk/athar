from decimal import Decimal

from app.config import settings


class SalesAgent:

    def __init__(self):
        self.product_name = settings.PRODUCT_NAME
        self.base_price = settings.PRICE_USDT
        self.max_discount = (
            settings.MAX_DISCOUNT_PERCENT
        )
        self.min_price = settings.MIN_PRICE_USDT

    def calculate_price(
        self,
        discount_percent=Decimal("0")
    ):
        discount_percent = Decimal(
            str(discount_percent)
        )

        if discount_percent < 0:
            discount_percent = Decimal("0")

        if discount_percent > self.max_discount:
            discount_percent = self.max_discount

        price = self.base_price * (
            Decimal("1")
            - discount_percent / Decimal("100")
        )

        if price < self.min_price:
            price = self.min_price

        return price.quantize(
            Decimal("0.01")
        )

    def can_offer_discount(
        self,
        discount_percent
    ):
        discount_percent = Decimal(
            str(discount_percent)
        )

        return (
            Decimal("0")
            <= discount_percent
            <= self.max_discount
        )

    def product_summary(self):
        return {
            "name": self.product_name,
            "price_usdt": str(
                self.base_price
            ),
            "minimum_price_usdt": str(
                self.min_price
            ),
            "subscription_days":
                settings.SUBSCRIPTION_DAYS,
            "network":
                settings.PAYMENT_NETWORK,
        }

    def answer(self, message: str):
        text = message.lower().strip()

        if any(
            word in text
            for word in [
                "price",
                "cost",
                "سعر",
                "السعر",
                "كم",
            ]
        ):
            return (
                f"{self.product_name} متاح بسعر "
                f"{self.base_price} USDT لمدة "
                f"{settings.SUBSCRIPTION_DAYS} يومًا."
            )

        if any(
            word in text
            for word in [
                "risk",
                "مخاطر",
                "خسارة",
                "ربح مضمون",
            ]
        ):
            return (
                "EXCORA أداة تحليل ومعلومات للسوق، "
                "ولا يضمن الأرباح ولا يخلو من المخاطر. "
                "القرار الاستثماري النهائي يعود للمستخدم."
            )

        if any(
            word in text
            for word in [
                "binance key",
                "api key",
                "مفتاح",
                "مفاتيح",
            ]
        ):
            return (
                "لا نطلب منك مشاركة المفتاح السري "
                "لحساب Binance أو أي مفتاح خاص."
            )

        if any(
            word in text
            for word in [
                "trade for me",
                "execute",
                "تداول عني",
                "نفذ الصفقة",
            ]
        ):
            return (
                "EXCORA لا ينفذ الصفقات نيابة عنك. "
                "هو يوفر أدوات التحليل والإشارات "
                "لمساعدتك في اتخاذ قرارك بنفسك."
            )

        return (
            "EXCORA PRO يوفر أدوات تحليل للسوق "
            "وإشارات ومعلومات تساعدك على دراسة "
            "الفرص وإدارة قراراتك. "
            f"الاشتراك {self.base_price} USDT لمدة "
            f"{settings.SUBSCRIPTION_DAYS} يومًا."
        )


sales_agent = SalesAgent()
