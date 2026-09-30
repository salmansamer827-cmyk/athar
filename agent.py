import os
from google import genai
from dotenv import load_dotenv
load_dotenv()  # هذا السطر يبحث عن ملف .env ويحمله كمتغيرات بيئة

# قراءة المتغيرات من الملف الخارجي .env
load_dotenv()

# تهيئة العميل (سيجلب المفتاح تلقائياً من ملف .env)
client = genai.Client()

# تعريف أداة حساب المساحة
def calculate_rectangle_area(length: float, width: float) -> float:
    """حساب مساحة المستطيل بناءً على الطول والعرض.
    Args:
        length: الطول
        width: العرض
    """
    return length * width

# إنشاء جلسة المحادثة المدعومة بالأداة
chat = client.chats.create(
    model="gemini-2.5-flash",
    config={
        "tools": [calculate_rectangle_area],
        "temperature": 0.0,
        "system_instruction": "أنت مساعد ذكاء اصطناعي دقيق. استخدم الأدوات البرمجية المتاحة لك لتنفيذ طلبات المستخدم."
    }
)

prompt = "أحتاج إلى حساب مساحة مستطيل طوله 15.5 وعرضه 6.2، الرجاء استخدام الأداة المخصصة لذلك."
print(f"المستخدم: {prompt}\n")

# إرسال الرسالة عبر الشات
response = chat.send_message(prompt)

print(f"الوكيل: {response.text}")
