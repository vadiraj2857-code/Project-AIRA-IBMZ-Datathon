import re
import spacy
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Set Page Configuration
st.set_page_config(page_title="Fraud & Privacy Shield", page_icon="🛡️", layout="wide")

# ---------------------------------------------------------
# LOAD SPACY & ML MODELS
# ---------------------------------------------------------
@st.cache_resource
def load_spacy_model():
    return spacy.load("en_core_web_sm")

@st.cache_resource
def build_scam_detector():
    # Training data fallback (SMS Spam Collection subset)
    training_data = [
        ("URGENT! You have won a $1,000 Walmart gift card. Click link to claim now!", "spam"),
        ("Your bank account ending in 4021 is suspended. Verify credentials immediately at http://fake-bank.com", "spam"),
        ("Free entry in 2 a wk weekly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121", "spam"),
        ("Congratulations! You are selected for a cash prize. Reply YES to claim.", "spam"),
        ("Hi mom, I will be home by 6 PM for dinner.", "ham"),
        ("Are we still meeting at the library for the group project tomorrow?", "ham"),
        ("Your OTP for secure login is 482910. Do not share this with anyone.", "ham"),
        ("Please review the attached project schedule document before Monday.", "ham")
    ]
    df = pd.DataFrame(training_data, columns=["text", "label"])
    
    # Train Naive Bayes Classifier with TF-IDF Vectorizer
    model = make_pipeline(TfidfVectorizer(stop_words='english'), MultinomialNB())
    model.fit(df["text"], df["label"])
    return model

nlp = load_spacy_model()
scam_model = build_scam_detector()

# ---------------------------------------------------------
# FEATURE 1: ENHANCED PII REDACTION ENGINE
# ---------------------------------------------------------
def sanitize_text(text):
    if not text.strip():
        return text
    
    # 1. Regex Rules for Numbers & Emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}+\b'
    card_pattern  = r'\b(?:\d[ -]*?){13,16}\b'
    
    # 2. Regex Rule for Common Name Patterns (e.g., "my name is alexa", "I am alex")
    name_intro_pattern = r'(?i)\b(my name is|i am|this is)\s+([a-zA-Z]+)\b'
    
    # Apply standard patterns
    text = re.sub(email_pattern, '[REDACTED_EMAIL]', text)
    text = re.sub(phone_pattern, '[REDACTED_PHONE]', text)
    text = re.sub(card_pattern, '[REDACTED_CARD]', text)
    
    # Redact names following intro phrases (catches lowercase names!)
    text = re.sub(name_intro_pattern, r'\1 [REDACTED_NAME]', text)
    
    # 3. SpaCy Named Entity Recognition for Capitalized Names & Locations
    doc = nlp(text)
    redacted_text = text
    
    for ent in reversed(doc.ents):
        if ent.label_ == "PERSON" and "[REDACTED" not in ent.text:
            redacted_text = redacted_text[:ent.start_char] + "[REDACTED_NAME]" + redacted_text[ent.end_char:]
        elif ent.label_ in ["GPE", "LOC"] and "[REDACTED" not in ent.text:
            redacted_text = redacted_text[:ent.start_char] + "[REDACTED_LOCATION]" + redacted_text[ent.end_char:]
            
    return redacted_text

# ---------------------------------------------------------
# FRONTEND DASHBOARD (STREAMLIT)
# ---------------------------------------------------------
st.title("🛡️ Project A.R.I.A.")
st.caption("Artificial Risk & Intelligence Agent — Fraud & Privacy Shield | Track 2: AI Secured")

st.info("🔒 Zero-Data Retention Policy: Inputs are processed in volatile memory and never stored or logged.")

tab1, tab2 = st.tabs(["🛡️ Feature 1: Privacy Masker (Outbound)", "🚨 Feature 2: Scam Detector (Inbound)"])

# TAB 1: OUTBOUND PRIVACY CLEANER
with tab1:
    st.subheader("Sanitize Private Information")
    st.write("Mask personal data (phones, emails, credit cards, names) before pasting text into online forms or public AI tools.")
    
    raw_input = st.text_area("Paste your text here:", height=150, placeholder="Example: Hi, my name is Alex. Call me at 9876543210 or email alex@example.com.")
    
    if st.button("Sanitize Text", type="primary"):
        if raw_input:
            clean_output = sanitize_text(raw_input)
            st.markdown("### Cleaned Output:")
            st.code(clean_output, language="text")
        else:
            st.warning("Please enter text to sanitize.")

# TAB 2: INBOUND SCAM DETECTOR
with tab2:
    st.subheader("Detect Phishing & Scam Messages")
    st.write("Analyze incoming SMS, WhatsApp, or email messages for fraud risk and psychological manipulation tactics.")
    
    scam_input = st.text_area("Paste suspicious message here:", height=150, placeholder="Example: URGENT! Your account is locked. Click link to verify.")
    
    if st.button("Scan Message Risk", type="primary"):
        if scam_input:
            prediction = scam_model.predict([scam_input])[0]
            probabilities = scam_model.predict_proba([scam_input])[0]
            scam_prob = probabilities[1] if len(probabilities) > 1 else 0.5
            
            st.markdown("### Safety Verdict:")
            if prediction == "spam" or scam_prob > 0.5:
                st.error(f"⚠️ **High Threat Detected!** Likelihood of Scam: {scam_prob * 100:.1f}%")
                
                # --- NEW UNIQUE FEATURE: PSYCHOLOGICAL TACTIC BREAKDOWN ---
                st.markdown("#### 🧠 A.R.I.A. Threat Intelligence Breakdown:")
                text_lower = scam_input.lower()
                
                tactics_found = []
                if any(w in text_lower for w in ['urgent', 'immediate', 'now', 'quickly', 'alert']):
                    tactics_found.append("🚨 **High Urgency / Panic Induction:** Forcing quick action before thinking.")
                if any(w in text_lower for w in ['bank', 'account', 'suspended', 'verify', 'credential', 'password']):
                    tactics_found.append("🏦 **Financial Impersonation:** Pretending to be a trusted institution.")
                if any(w in text_lower for w in ['win', 'prize', 'gift', 'cash', 'reward', 'congratulations']):
                    tactics_found.append("🎁 **Lure & Reward Trap:** Using fake winnings to grab attention.")
                if any(w in text_lower for w in ['http', 'www', '.com', '.net', 'click', 'link']):
                    tactics_found.append("🔗 **Malicious Link Injection:** Directing user to an external phishing site.")
                
                if not tactics_found:
                    tactics_found.append("⚠️ **General Social Engineering Pattern:** Detected linguistic anomalies.")
                    
                for tactic in tactics_found:
                    st.warning(tactic)
                # ---------------------------------------------------------
                
            else:
                st.success(f"✅ **Message Appears Safe.** Likelihood of Scam: {scam_prob * 100:.1f}%")
        else:
            st.warning("Please enter a message to analyze.")