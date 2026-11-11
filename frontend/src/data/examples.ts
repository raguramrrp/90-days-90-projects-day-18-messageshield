import type { ThreatCategory } from "../types/messageshield";

export interface DemoMessageExample {
  id: string;
  title: string;
  senderTag: string;
  expectedCategory: ThreatCategory;
  expectedRisk: "Low" | "Medium" | "High" | "Critical";
  message: string;
  explanation: string;
}

export const DEMO_EXAMPLES: DemoMessageExample[] = [
  {
    id: "normal-appointment",
    title: "Normal Appointment Notification",
    senderTag: "JD-CLINIC-S",
    expectedCategory: "Safe / Normal",
    expectedRisk: "Low",
    message:
      "Reminder: Your dental consultation at Sample Care Clinic is scheduled for tomorrow at 10:30 AM. Reply YES to confirm.",
    explanation:
      "Routine appointment confirmation with no links, payment demand, urgency coercion, or credential request.",
  },
  {
    id: "legit-bank-txn",
    title: "Legitimate Bank Transaction Alert",
    senderTag: "AD-DMOBNK-T",
    expectedCategory: "Safe / Normal",
    expectedRisk: "Low",
    message:
      "A/c XX0000 debited for INR 1,450.00 on 11-11-26 at DemoMart via Ref No. 000000000000. If not done by you, call 1800-000-0000 or block card in official SampleBank app. Never share OTP.",
    explanation:
      "Verified TRAI Transactional header (-T) matching SampleBank, defensive OTP warning, and demo toll-free helpline.",
  },
  {
    id: "promo-offer",
    title: "Promotional Retail Offer",
    senderTag: "VK-DMOBSK-P",
    expectedCategory: "Promotional",
    expectedRisk: "Low",
    message:
      "DemoMart Weekend Sale: Flat 20% off on fresh groceries above Rs.999. Use code DEMO20 in the DemoMart app before Sunday. T&C apply. Reply STOP to opt out.",
    explanation:
      "Marketing (-P) offer referencing an in-app coupon code and opt-out instruction without suspicious links.",
  },
  {
    id: "fake-kyc",
    title: "Fake Bank KYC Suspension",
    senderTag: "VK-DMOKYC",
    expectedCategory: "Phishing",
    expectedRisk: "Critical",
    message:
      "Dear customer, your SampleBank account KYC has expired today. Your account will be blocked within 2 hours. Update KYC immediately at http://samplebank-kyc.xyz/verify",
    explanation:
      "Campaign Sample #1: Urgent 2-hour threat paired with mismatched DLT header, official SampleBank lookup (1800-000-0000), and Defanged Family Warning.",
  },
  {
    id: "campaign-rotated-kyc",
    title: "Campaign Variant: Rotated Bank KYC Link",
    senderTag: "JM-DMOKYC-P",
    expectedCategory: "Phishing",
    expectedRisk: "Critical",
    message:
      "Dear customer, your SampleBank account KYC has expired today. Your account will be blocked within 2 hours. Update KYC immediately at http://samplebank-fresh.top/verify",
    explanation:
      "Campaign Sample #2: Scan right after Sample #1 above to trigger Recurring Scam Campaign Match (rotated domain from samplebank-kyc.xyz) + Promotional (-P) DLT header misuse.",
  },
  {
    id: "upi-qr-link",
    title: "UPI Cashback Deep-Link Bait",
    senderTag: "+91 00000 00001",
    expectedCategory: "Financial Scam",
    expectedRisk: "Critical",
    message:
      "Congrats! Claim your Rs.4,999 festive cashback right now using your verified payout link: upi://pay?pa=demo-cashback@exampleupi&pn=Demo%20Reward&am=4999&cu=INR",
    explanation:
      "Dummy telephone number pushing an outgoing upi://pay link disguised as incoming cashback.",
  },
  {
    id: "upi-mandate-autopay",
    title: "UPI AutoPay Mandate & Refund Trap",
    senderTag: "JX-REFUND-P",
    expectedCategory: "Financial Scam",
    expectedRisk: "Critical",
    message:
      "SampleRail Ticket Refund Rs.3,200 approved! Confirm refund mandate inside your UPI app: upi://mandate?pa=demo-refund@testupi&pn=Demo%20Refund&am=3200&cu=INR&tn=Demo",
    explanation:
      "Dissects upi://mandate AutoPay recurring debit traps, decodes the TRAI Promotional (-P) header (JX-REFUND-P), and neutralizes upi[:]// links in Safe Family Warnings.",
  },
  {
    id: "homoglyph-spoof",
    title: "Zero-Width & '@' Redirect Link Spoof",
    senderTag: "JX-DMOLNK-P",
    expectedCategory: "Phishing",
    expectedRisk: "Critical",
    message:
      "Urgent: Re-verify your S\u200ba\u200bm\u200bp\u200bl\u200beBank profile with O\u200bT\u200bP before midnight at https://samplebank.example@demo-redirect.xyz/auth",
    explanation:
      "Uses invisible zero-width characters inside SampleBank/OTP plus an '@' credential-redirect trick pointing to demo-redirect.xyz.",
  },
  {
    id: "cyrillic-lookalike-sbi",
    title: "Cyrillic Homoglyph & Punycode Spoof",
    senderTag: "+91 00000 00002",
    expectedCategory: "Phishing",
    expectedRisk: "Critical",
    message:
      "SampleBank Alert: Unusual login from unknown device. Secure your profile now at https://\u0455amplebank-secure.xyz/login or xn--smplbnk-k4a.top before block.",
    explanation:
      "Mixes Cyrillic '\u0455' lookalike + Punycode domain with a dummy mobile number claiming to be SampleBank.",
  },
  {
    id: "electricity-mobile-spoof",
    title: "Electricity Cut-Off Mobile Spoof",
    senderTag: "+91 00000 00002",
    expectedCategory: "Impersonation",
    expectedRisk: "Critical",
    message:
      "URGENT: Your electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Call electricity officer immediately on +91 00000 00002.",
    explanation:
      "Flags mobile-number utility impersonation, pairs with National Electricity Helpline 1912, and shows Shared Phone Campaign Match if scanned after the Cyrillic sample.",
  },
  {
    id: "fake-courier",
    title: "Fake Courier Redelivery Fee",
    senderTag: "+91 00000 00003",
    expectedCategory: "Financial Scam",
    expectedRisk: "Critical",
    message:
      "Sample Parcel Service: Your parcel DEMO000001 is held at sorting hub due to incomplete address. Pay Rs.25 redelivery fee within 12 hrs at http://parcel-redelivery-demo.xyz/pay",
    explanation:
      "Dummy mobile number impersonating a parcel service with a small Rs.25 fee, lookalike .xyz link, and official verification card.",
  },
  {
    id: "fake-job",
    title: "Fake Work-From-Home Job Fee",
    senderTag: "HR-TASK",
    expectedCategory: "Financial Scam",
    expectedRisk: "Critical",
    message:
      "Part-time Work From Home! Earn Rs.3,500 daily by rating sample videos online. Pay Rs.499 registration fee to activate account. Message +91-0000000001",
    explanation:
      "Unrealistic daily income tied to an upfront registration fee and off-platform contact number.",
  },
  {
    id: "otp-theft",
    title: "OTP & Screen-Share Theft",
    senderTag: "+91 00000 00004",
    expectedCategory: "OTP / Credential Theft",
    expectedRisk: "Critical",
    message:
      "Your debit card Rs.9,999 transaction is pending. Share your 6-digit OTP immediately or install a remote screen-share app to cancel the charge.",
    explanation:
      "Asks for a sensitive OTP and remote screen-sharing app under panic — triggers Airplane Mode Golden-Hour recovery triage.",
  },
  {
    id: "apk-echallan-malware",
    title: "Fake E-Challan .APK / Remote Trap",
    senderTag: "+91 00000 00005",
    expectedCategory: "OTP / Credential Theft",
    expectedRisk: "Critical",
    message:
      "Traffic E-Challan Notice (Demo): Vehicle fine Rs.2,000 pending. Download Demo_Challan.apk from http://demo-challan-pay.icu/app or install a remote screen-share app to settle now.",
    explanation:
      "Combines suspicious .apk malware link + remote access prompt — triggers Airplane Mode containment & 1930 Recovery Triage.",
  },
  {
    id: "upi-scam",
    title: "UPI Collect-Request Trap",
    senderTag: "DMOCBK",
    expectedCategory: "Financial Scam",
    expectedRisk: "Critical",
    message:
      "Congratulations! You received Rs.4,999 UPI cashback reward. Approve the pending UPI collect request and enter your UPI PIN to claim before tonight.",
    explanation:
      "Classic UPI collect scam: entering a UPI PIN always authorizes outgoing payment, never incoming cashback.",
  },
  {
    id: "fake-reward",
    title: "Fake Prize / IP-Link Reward",
    senderTag: "DMOWIN",
    expectedCategory: "Fake Reward",
    expectedRisk: "Critical",
    message:
      "Lucky Winner! You won a flagship smartphone in festive draw. Claim your reward now at http://198.51.100.22/claim?token=demo99",
    explanation:
      "Unsolicited prize paired with a documentation test IP-address HTTP link and suspicious token query parameter.",
  },
];

export const SAFETY_TIPS: { title: string; body: string }[] = [
  {
    title: "UPI PIN & QR Code Rule",
    body: "You never need to scan a QR code or enter your UPI PIN to receive money, refunds, or cashback.",
  },
  {
    title: "TRAI Header Check",
    body: "Real institutions and utilities use registered alphabetic headers (like AD-DMOBNK-T), never personal 10-digit mobile numbers.",
  },
  {
    title: "Warn Family Safely",
    body: "Always neutralize links (hxxp://) before forwarding scam screenshots or warnings to family members.",
  },
];
