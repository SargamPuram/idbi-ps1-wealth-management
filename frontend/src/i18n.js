// Lightweight, hand-written localization for chrome text (Gemini itself replies
// in the requested language for the actual conversation — this file only covers
// the static welcome message + a few UI labels so the demo feels multilingual
// even for parts that don't go through the AI).
export const WELCOME_MESSAGES = {
  English: "Namaste! I'm Dhanvi, your personal wealth advisor at IDBI Bank. How can I help you today?",
  Hindi: "नमस्ते! मैं धनवी हूं, IDBI बैंक में आपकी निजी वेल्थ एडवाइजर। आज मैं आपकी कैसे मदद कर सकती हूं?",
  Tamil: "வணக்கம்! நான் தன்வி, IDBI வங்கியில் உங்கள் தனிப்பட்ட செல்வ ஆலோசகர். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
  Telugu: "నమస్తే! నేను ధన్వి, IDBI బ్యాంక్‌లో మీ వ్యక్తిగత సంపద సలహాదారుని. ఈరోజు నేను మీకు ఎలా సహాయపడగలను?",
  Bengali: "নমস্তে! আমি ধন্বী, IDBI ব্যাংকে আপনার ব্যক্তিগত ওয়েলথ অ্যাডভাইজার। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
  Marathi: "नमस्ते! मी धनवी, IDBI बँकेतील तुमची वैयक्तिक वेल्थ अ‍ॅडव्हायझर. आज मी तुम्हाला कशी मदत करू शकते?",
};

export const QUICK_ACTIONS = [
  { icon: "📊", label: "My Portfolio", message: "Can you give me a quick summary of my portfolio?" },
  { icon: "🎯", label: "Plan a Goal", message: "I want to plan for a financial goal. Can you help?" },
  { icon: "📈", label: "Market Update", message: "What's happening in the markets today and how does it affect me?" },
  { icon: "💡", label: "Investment Ideas", message: "What are some good investment ideas for me right now?" },
  { icon: "🔄", label: "Rebalance", message: "Should I rebalance my portfolio?" },
];
