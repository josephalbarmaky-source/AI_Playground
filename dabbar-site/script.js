// Bilingual content
const I18N = {
    en: {
        "nav.features": "Features",
        "nav.pricing": "Pricing",
        "nav.how": "How it works",
        "nav.cta": "Get early access",

        "hero.badge": "Private beta — UAE only",
        "hero.title1": "Your personal AI assistant,",
        "hero.title2": "on Telegram.",
        "hero.sub": "Dabbar handles your calendar, email, reminders, and tasks — 24/7, in Arabic or English. Built for the UAE. <strong>AED 500/month</strong> instead of AED 5,000 for a human VA.",
        "hero.cta": "Get early access",
        "hero.cta2": "See how it works →",
        "hero.meta1": "✦ No credit card",
        "hero.meta2": "✦ Arabic & English",
        "hero.meta3": "✦ Private — your data stays in the UAE",

        "problem.pill": "The problem",
        "problem.title": "Human VAs cost too much. ChatGPT doesn't know your life.",
        "problem.vaLabel": "Human VA in UAE",
        "problem.va1": "✖ 9–5 working hours only",
        "problem.va2": "✖ Visa, salary, holidays, sick days",
        "problem.va3": "✖ Takes weeks to hire",
        "problem.gptLabel": "ChatGPT / generic bots",
        "problem.gpt1": "✖ Doesn't know your calendar",
        "problem.gpt2": "✖ Can't send real emails",
        "problem.gpt3": "✖ Banned from WhatsApp (Jan 2026)",
        "problem.da1": "✓ 24/7 — never sleeps",
        "problem.da2": "✓ Calendar, email, tasks, web",
        "problem.da3": "✓ Arabic & English, Gulf dialect",

        "features.pill": "What Dabbar does",
        "features.title": "A real assistant, not a chatbot.",
        "features.f1t": "Calendar management",
        "features.f1d": "\"What's on my calendar tomorrow?\" \"Move my 3pm to 4pm.\" It just works.",
        "features.f2t": "Email drafting & triage",
        "features.f2d": "Summarise your inbox, draft replies, send — all from Telegram.",
        "features.f3t": "Reminders & follow-ups",
        "features.f3d": "\"Remind me to call Fatima in 2 hours.\" Dabbar never forgets.",
        "features.f4t": "Tasks & to-dos",
        "features.f4d": "Add, list, complete — in natural language. No apps to manage.",
        "features.f5t": "Web research",
        "features.f5d": "Real answers from real sources. No hallucinations, with citations.",
        "features.f6t": "Expense tracking",
        "features.f6d": "Send a receipt photo, Dabbar categorises and tracks your spend.",

        "how.pill": "Three steps",
        "how.title": "From zero to assistant in 60 seconds.",
        "how.s1t": "Open Telegram",
        "how.s1d": "Search @DabbarBot or scan the QR on our site.",
        "how.s2t": "Say hi",
        "how.s2d": "Tap Start. Dabbar greets you in your language automatically.",
        "how.s3t": "Let it handle things",
        "how.s3d": "Reminders, calendar, email, tasks — just ask, like you would a real assistant.",

        "pricing.pill": "Simple pricing",
        "pricing.title": "One plan. Cancel anytime.",
        "pricing.badge": "Launch price — first 100 users",
        "pricing.period": "/month",
        "pricing.was": "Normally AED 750/month",
        "pricing.feat1": "✓ Unlimited conversations",
        "pricing.feat2": "✓ Calendar + Gmail integration",
        "pricing.feat3": "✓ Unlimited reminders & tasks",
        "pricing.feat4": "✓ Web search with citations",
        "pricing.feat5": "✓ Arabic & English (Gulf dialect)",
        "pricing.feat6": "✓ Private — your data stays in the UAE",
        "pricing.feat7": "✓ 7-day free trial, no card needed",
        "pricing.cta": "Join the waitlist",

        "wait.title": "Be among the first 100.",
        "wait.sub": "We're rolling out invites in waves. Drop your Telegram and email and we'll reach out.",
        "wait.cta": "Join waitlist",
        "wait.success": "You're in. We'll be in touch soon.",

        "footer.tag": "Your AI personal assistant, on Telegram.",
        "footer.privacy": "Privacy",
        "footer.terms": "Terms",
    },
    ar: {
        "nav.features": "المميزات",
        "nav.pricing": "الأسعار",
        "nav.how": "كيف يعمل",
        "nav.cta": "سجّل الآن",

        "hero.badge": "نسخة تجريبية — للإمارات فقط",
        "hero.title1": "مساعدك الشخصي بالذكاء الاصطناعي،",
        "hero.title2": "على تيليجرام.",
        "hero.sub": "دبّر يدير كالندرك، إيميلاتك، تذكيراتك، ومهامك — ٢٤ ساعة، بالعربي أو الإنجليزي. مصمم للإمارات. <strong>٥٠٠ درهم شهرياً</strong> بدال ٥٠٠٠ درهم لمساعد شخصي.",
        "hero.cta": "سجّل الآن",
        "hero.cta2": "شوف كيف يشتغل ←",
        "hero.meta1": "✦ بدون بطاقة ائتمان",
        "hero.meta2": "✦ عربي وإنجليزي",
        "hero.meta3": "✦ خصوصية — بياناتك تبقى في الإمارات",

        "problem.pill": "المشكلة",
        "problem.title": "المساعد البشري غالي. وChatGPT ما يعرف حياتك.",
        "problem.vaLabel": "مساعد بشري في الإمارات",
        "problem.va1": "✖ يشتغل دوام فقط",
        "problem.va2": "✖ فيزا، راتب، إجازات، أيام مرضية",
        "problem.va3": "✖ يحتاج أسابيع للتوظيف",
        "problem.gptLabel": "ChatGPT / بوتات عادية",
        "problem.gpt1": "✖ ما يعرف كالندرك",
        "problem.gpt2": "✖ ما يقدر يرسل إيميلات فعلية",
        "problem.gpt3": "✖ ممنوع من واتساب (يناير ٢٠٢٦)",
        "problem.da1": "✓ ٢٤ ساعة — ما ينام",
        "problem.da2": "✓ كالندر، إيميل، مهام، بحث",
        "problem.da3": "✓ عربي وإنجليزي، باللهجة الخليجية",

        "features.pill": "وش يسوي دبّر",
        "features.title": "مساعد حقيقي، مو مجرد بوت.",
        "features.f1t": "إدارة الكالندر",
        "features.f1d": "\"وش عندي بكرة؟\" \"حوّل اجتماع الثلاث للأربع.\" يشتغل ببساطة.",
        "features.f2t": "كتابة وفرز الإيميلات",
        "features.f2d": "لخّص الإنبوكس، اكتب الردود، أرسلها — كلها من تيليجرام.",
        "features.f3t": "تذكيرات ومتابعة",
        "features.f3d": "\"ذكرني أتصل بفاطمة بعد ساعتين.\" دبّر ما ينسى.",
        "features.f4t": "المهام والقوائم",
        "features.f4d": "أضف، اعرض، كمّل — كلها بلغة طبيعية. بدون تطبيقات.",
        "features.f5t": "بحث بالإنترنت",
        "features.f5d": "إجابات حقيقية من مصادر حقيقية. بدون اختراع، مع المصادر.",
        "features.f6t": "تتبع المصاريف",
        "features.f6d": "ابعث صورة فاتورة، دبّر يصنّفها ويتبع مصاريفك.",

        "how.pill": "ثلاث خطوات",
        "how.title": "من الصفر لمساعد في ٦٠ ثانية.",
        "how.s1t": "افتح تيليجرام",
        "how.s1d": "ابحث @DabbarBot أو اسكن QR من موقعنا.",
        "how.s2t": "سلّم عليه",
        "how.s2d": "اضغط Start. دبّر يرحّب فيك بلغتك تلقائياً.",
        "how.s3t": "خلّه يتصرّف",
        "how.s3d": "تذكيرات، كالندر، إيميل، مهام — اطلب، مثل أي مساعد حقيقي.",

        "pricing.pill": "سعر بسيط",
        "pricing.title": "خطة واحدة. ألغِ متى ما تبي.",
        "pricing.badge": "سعر الإطلاق — أول ١٠٠ مستخدم",
        "pricing.period": "/شهرياً",
        "pricing.was": "السعر العادي ٧٥٠ درهم شهرياً",
        "pricing.feat1": "✓ محادثات بدون حد",
        "pricing.feat2": "✓ تكامل مع الكالندر والإيميل",
        "pricing.feat3": "✓ تذكيرات ومهام بدون حد",
        "pricing.feat4": "✓ بحث بالإنترنت مع المصادر",
        "pricing.feat5": "✓ عربي وإنجليزي (اللهجة الخليجية)",
        "pricing.feat6": "✓ خصوصية — بياناتك تبقى في الإمارات",
        "pricing.feat7": "✓ ٧ أيام تجربة مجانية، بدون بطاقة",
        "pricing.cta": "انضم للقائمة",

        "wait.title": "كن من أول ١٠٠ مستخدم.",
        "wait.sub": "نطلق الدعوات على دفعات. اكتب تيليجرامك وإيميلك ونتواصل معك.",
        "wait.cta": "انضم للقائمة",
        "wait.success": "تم تسجيلك. نتواصل معك قريباً.",

        "footer.tag": "مساعدك الشخصي بالذكاء الاصطناعي، على تيليجرام.",
        "footer.privacy": "الخصوصية",
        "footer.terms": "الشروط",
    },
};

function applyLang(lang) {
    const html = document.documentElement;
    html.setAttribute("lang", lang);
    html.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");
    html.setAttribute("data-lang", lang);

    const dict = I18N[lang];
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key] !== undefined) {
            el.innerHTML = dict[key];
        }
    });

    const label = document.getElementById("lang-label");
    if (label) label.textContent = lang === "ar" ? "English" : "العربية";

    try { localStorage.setItem("dabbar-lang", lang); } catch (e) {}
}

function toggleLang() {
    const current = document.documentElement.getAttribute("data-lang") || "en";
    applyLang(current === "en" ? "ar" : "en");
}

async function submitWaitlist(e) {
    e.preventDefault();
    const tg = document.getElementById("tg").value.trim();
    const email = document.getElementById("email").value.trim();
    if (!tg || !email) return false;

    // Try to POST to the real backend; fall back to localStorage if offline.
    try {
        const resp = await fetch("/api/dabbar/waitlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg, email }),
        });
        if (!resp.ok) throw new Error("backend error");
    } catch (err) {
        try {
            const saved = JSON.parse(localStorage.getItem("dabbar-waitlist") || "[]");
            saved.push({ tg, email, at: new Date().toISOString() });
            localStorage.setItem("dabbar-waitlist", JSON.stringify(saved));
        } catch (e2) {}
    }

    document.getElementById("waitSuccess").classList.add("show");
    document.querySelector(".waitlist-form").reset();
    return false;
}

// Boot
(function init() {
    let saved = null;
    try { saved = localStorage.getItem("dabbar-lang"); } catch (e) {}
    const detected = saved || (navigator.language && navigator.language.startsWith("ar") ? "ar" : "en");
    applyLang(detected);
})();
