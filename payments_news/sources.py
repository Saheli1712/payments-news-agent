"""Economic Times feeds to read, and the words that make a story "payments" news.

Feed IDs on ET change from time to time. If one of these stops working, open
https://economictimes.indiatimes.com/rss.cms in a browser, copy the new feed URL
and paste it here (or pass --feed on the command line).
"""

ET_RSS_INDEX = "https://economictimes.indiatimes.com/rss.cms"

FEEDS = {
    # ETBFSI (ET's banking, financial services and insurance site)
    "ETBFSI Payments": "https://bfsi.economictimes.indiatimes.com/rss/payments",
    "ETBFSI Fintech": "https://bfsi.economictimes.indiatimes.com/rss/fintech",
    "ETBFSI Top stories": "https://bfsi.economictimes.indiatimes.com/rss/topstories",
    # Main Economic Times site
    "ET Banking/Finance": "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358319.cms",
    "ET Tech Fintech": "https://economictimes.indiatimes.com/tech/fintech/rssfeeds/78570530.cms",
}

# Feeds whose stories are all payments stories, so no keyword filter is applied.
PAYMENTS_ONLY_FEEDS = {"ETBFSI Payments"}

# Lower-case keywords; a story matches if any appears in its title or summary.
PAYMENTS_KEYWORDS = [
    "payment", "payments", "upi", "npci", "neft", "rtgs", "imps", "bbps",
    "rupay", "wallet", "prepaid", "ppi", "credit card", "debit card", "card network",
    "visa", "mastercard", "paytm", "phonepe", "google pay", "gpay", "razorpay",
    "cashfree", "pine labs", "bharatpe", "mobikwik", "payu", "billdesk",
    "payment aggregator", "payment gateway", "merchant", "pos terminal",
    "qr code", "e-rupee", "cbdc", "digital rupee", "remittance", "cross-border",
    "tokenisation", "tokenization", "mdr", "fastag", "aeps", "upi lite",
    "upi 123pay", "autopay", "e-mandate", "bnpl", "buy now pay later",
]
