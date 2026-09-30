from urllib.parse import urlparse


class LeadQualificationEngine:

    def __init__(self):

        # مواقع ومصادر نعرف أنها ليست عملاء محتملين مباشرين
        self.blocked_domains = {
            "youtube.com",
            "youtu.be",
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "reddit.com",
            "wikipedia.org",
            "medium.com",
            "hubspot.com",
            "taskade.com",
            "godaddy.com",
            "lumay.ai",
            "designrush.com",
            "toolradar.com"
        }

        # كلمات تدل غالبًا على أن الصفحة مقال/دليل/مقارنة
        self.content_keywords = [
            "best ",
            "top ",
            "guide",
            "blog",
            "news",
            "article",
            "tools",
            "tool",
            "companies",
            "company list",
            "comparison",
            "compare",
            "review",
            "ranking",
            "ranked",
            "2026",
            "examples",
            "how to",
            "resources"
        ]

        # إشارات إلى نشاط تجاري حقيقي
        self.business_keywords = [
            "services",
            "service",
            "solutions",
            "contact us",
            "about us",
            "our team",
            "get started",
            "request a quote",
            "book a consultation",
            "customers",
            "clients",
            "pricing",
            "products",
            "locations"
        ]

        # إشارات إلى احتياج محتمل للأتمتة
        self.need_keywords = [
            "customer support",
            "customer service",
            "lead generation",
            "sales",
            "marketing",
            "appointments",
            "booking",
            "inquiries",
            "workflow",
            "operations",
            "data entry",
            "email",
            "crm",
            "scheduling",
            "administration",
            "support"
        ]

    def get_domain(self, url: str):

        try:

            domain = urlparse(url).netloc.lower()

            if domain.startswith("www."):
                domain = domain[4:]

            return domain

        except Exception:

            return ""

    def is_blocked_domain(self, domain: str):

        for blocked in self.blocked_domains:

            if (
                domain == blocked
                or domain.endswith("." + blocked)
            ):
                return True

        return False

    def is_content_page(
        self,
        title: str,
        snippet: str
    ):

        text = (
            f"{title} {snippet}"
        ).lower()

        matches = []

        for keyword in self.content_keywords:

            if keyword in text:
                matches.append(keyword)

        # وجود عدة إشارات محتوى يعني غالبًا أنها مقالة
        return len(matches) >= 2

    def detect_business_signals(
        self,
        title: str,
        snippet: str
    ):

        text = (
            f"{title} {snippet}"
        ).lower()

        signals = []

        for keyword in self.business_keywords:

            if keyword in text:
                signals.append(keyword)

        return signals

    def detect_needs(
        self,
        title: str,
        snippet: str
    ):

        text = (
            f"{title} {snippet}"
        ).lower()

        needs = []

        for keyword in self.need_keywords:

            if keyword in text:
                needs.append(keyword)

        return needs

    def qualify(self, results):

        leads = []

        print()
        print("=" * 60)
        print("LEAD QUALIFICATION ENGINE")
        print("=" * 60)

        for result in results:

            title = result.get(
                "title",
                ""
            )

            url = result.get(
                "url",
                ""
            )

            snippet = result.get(
                "snippet",
                ""
            )

            domain = self.get_domain(url)

            if not domain:

                continue

            # -------------------------------------------------
            # 1. استبعاد المواقع غير المناسبة
            # -------------------------------------------------

            if self.is_blocked_domain(domain):

                print(
                    f"[FILTERED] {domain} "
                    f"→ blocked domain"
                )

                continue

            # -------------------------------------------------
            # 2. استبعاد المقالات والمقارنات
            # -------------------------------------------------

            if self.is_content_page(
                title,
                snippet
            ):

                print(
                    f"[FILTERED] {title} "
                    f"→ content/article"
                )

                continue

            # -------------------------------------------------
            # 3. البحث عن إشارات شركة حقيقية
            # -------------------------------------------------

            business_signals = (
                self.detect_business_signals(
                    title,
                    snippet
                )
            )

            if not business_signals:

                print(
                    f"[LOW FIT] {domain} "
                    f"→ no business signals"
                )

                continue

            # -------------------------------------------------
            # 4. البحث عن احتياج محتمل
            # -------------------------------------------------

            needs = self.detect_needs(
                title,
                snippet
            )

            if not needs:

                print(
                    f"[LOW FIT] {domain} "
                    f"→ no automation need detected"
                )

                continue

            # -------------------------------------------------
            # 5. تحديد مستوى الملاءمة
            # -------------------------------------------------

            score = (
                len(business_signals)
                + len(needs) * 2
            )

            if score >= 8:

                fit = "HIGH"

            elif score >= 5:

                fit = "MEDIUM"

            else:

                fit = "LOW"

            # -------------------------------------------------
            # 6. إنشاء Lead
            # -------------------------------------------------

            lead = {

                "business": title,

                "website": url,

                "domain": domain,

                "business_signals":
                    business_signals,

                "potential_needs":
                    needs,

                "score":
                    score,

                "fit":
                    fit,

                "status":
                    "PROSPECT"
            }

            leads.append(lead)

            print()
            print(
                f"[LEAD {len(leads)}]"
            )

            print(
                f"Business: "
                f"{lead['business']}"
            )

            print(
                f"Website: "
                f"{lead['website']}"
            )

            print(
                f"Business Signals: "
                f"{', '.join(business_signals)}"
            )

            print(
                f"Potential Needs: "
                f"{', '.join(needs)}"
            )

            print(
                f"Score: "
                f"{score}"
            )

            print(
                f"Fit: "
                f"{fit}"
            )

            print(
                f"Status: "
                f"PROSPECT"
            )

        print()
        print("=" * 60)
        print(
            f"Qualified leads: "
            f"{len(leads)}"
        )
        print("=" * 60)

        return leads
