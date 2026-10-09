"""Publisher RSS feeds and the words that make a story payments news.

ET feed IDs can change from time to time. If one stops working, check
https://economictimes.indiatimes.com/rss.cms for its replacement.
"""

ET_RSS_INDEX = "https://economictimes.indiatimes.com/rss.cms"

FEEDS = {
    # India-focused publisher feeds
    "ET Banking/Finance": "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358319.cms",
    "ET Tech Fintech": "https://economictimes.indiatimes.com/tech/fintech/rssfeeds/78570530.cms",
    "Mint Industry": "https://www.livemint.com/rss/industry",
    "Mint Money": "https://www.livemint.com/rss/money",
    # Global financial and payment-industry publisher feeds
    "Financial Times Financial Services": "https://www.ft.com/rss/companies/financial-services",
    "Payments Dive": "https://www.paymentsdive.com/feeds/news/",
    "PYMNTS": "https://www.pymnts.com/feed/",
}

# Publisher feeds focused exclusively on the payment industry.
PAYMENTS_ONLY_FEEDS = {"Payments Dive"}

# Lower-case keywords; a story matches if any appears in its title or summary.
PAYMENTS_KEYWORDS = [
    "payment", "upi", "npci", "neft", "rtgs", "imps", "bbps", "ach", "rtp",
    "fednow", "sepa", "faster payments", "instant payment", "real-time payment",
    "real time payment", "account-to-account", "account to account",
    "payment rail", "payment rails", "rupay", "wallet", "prepaid", "ppi",
    "payment system", "payment service", "payment provider", "payment platform",
    "payment processor", "payment processing", "payment infrastructure",
    "payments industry", "payment transaction", "payment transactions",
    "credit card", "debit card", "card network", "card issuer", "card issuing",
    "card acquirer", "card acquiring", "card payment", "card payments",
    "interchange fee", "visa", "mastercard", "paytm", "phonepe", "google pay",
    "gpay", "razorpay", "cashfree", "pine labs", "bharatpe", "mobikwik",
    "payu", "billdesk", "payment aggregator", "payment gateway", "pos terminal",
    "qr code", "e-rupee", "cbdc", "digital rupee", "remittance",
    "cross-border payment", "cross border payment", "tokenisation",
    "tokenization", "mdr", "fastag", "aeps", "upi lite", "upi 123pay",
    "autopay", "e-mandate", "bnpl", "buy now pay later", "swift payment",
    "swift network", "swift gpi", "iso 20022",
]
