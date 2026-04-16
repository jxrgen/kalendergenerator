import streamlit as st
import pandas as pd
import pdfplumber
from datetime import datetime
import io

# Konfiguration
st.set_page_config(page_title="G/AIH Kalender", page_icon="📅", layout="wide")

def create_ics(df):
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GAiH//Kalender//DA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    for _, row in df.iterrows():
        date_obj = datetime.strptime(row['Start Date'], "%m/%d/%Y")
        date_str = date_obj.strftime("%Y%m%d")
        ics_lines.append("BEGIN:VEVENT")
        ics_lines.append(f"SUMMARY:{row['Subject']}")
        ics_lines.append(f"DTSTART:{date_str}T193000")
        ics_lines.append(f"DTEND:{date_str}T220000")
        ics_lines.append(f"DESCRIPTION:{row['Description']}")
        ics_lines.append(f"LOCATION:{row['Location']}")
        ics_lines.append("END:VEVENT")
    ics_lines.append("END:VCALENDAR")
    return "\n".join(ics_lines)

def parse_pdf(file):
    all_events = []
    month_map = {
        "Marts": 3, "April": 4, "Maj": 5, "Juni": 6, "August": 8, 
        "September": 9, "Oktober": 10, "November": 11, "December": 12, 
        "Januar": 1, "Februar": 2
    }
    with pdfplumber.open(file) as pdf:
        table = pdf.pages[0].extract_table()
        if not table: return None
        for row in table[1:]:
            if not row[0]: continue
            m_name = row[0].strip()
            m_num = month_map.get(m_name)
            if not m_num: continue
            year = 2026 if m_num >= 3 else 2027
            types = [("Bogruppemøde", 2), ("Bestyrelsesmøde", 3), ("Månedsmøde", 4), ("Generalforsamling", 5)]
            for title, idx in types:
                day_val = row[idx].replace('\n', '').strip() if row[idx] else ""
                if day_val and day_val.isdigit():
                    desc = f"Boggruppe {row[6].strip()} er vært" if idx >= 4 else ""
                    d_str = f"{m_num:02d}/{int(day_val):02d}/{year}"
                    all_events.append({
                        "Subject": title, "Start Date": d_str, "Start Time": "19:30",
                        "End Date": d_str, "End Time": "22:00", "Description": desc,
                        "Location": "G/AIH", "All Day Event": "False", "Private": "False"
                    })
    return pd.DataFrame(all_events)

st.title("📅 G/AIH Kalender Generator")
uploaded_file = st.file_uploader("Upload G/AIH PDF-kalender", type="pdf")

if uploaded_file:
    df = parse_pdf(uploaded_file)
    if df is not None:
        st.success(f"Fundet {len(df)} begivenheder")
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("1. Vælg dit format og hent filen")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("🔵 Google Kalender (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "google_kalender.csv", "text/csv", use_container_width=True)
        with col2:
            st.download_button("🔴 Microsoft Outlook (CSV)", df.to_csv(index=False).encode('utf-16'), "outlook_kalender.csv", "text/csv", use_container_width=True)
        with col3:
            st.download_button("🍏 Apple Kalender (ICS)", create_ics(df), "apple_kalender.ics", "text/calendar", use_container_width=True)
            
        st.divider()
        st.subheader("2. Sådan importerer du filen")
        
        with st.expander("🔵 Vejledning til Google Kalender"):
            st.write("""
            1. Åbn **calendar.google.com** på en computer.
            2. Klik på **Indstillinger** (tandhjulet øverst til højre).
            3. Vælg **Import og eksport** i menuen til venstre.
            4. Vælg filen `google_kalender.csv` og klik på **Importér**.
            """)
            
        with st.expander("🔴 Vejledning til Microsoft Outlook"):
            st.write("""
            1. Åbn Outlook på din computer.
            2. Gå til **Filer** > **Åbn og eksportér** > **Importér/eksportér**.
            3. Vælg **Importér fra et andet program eller fil** -> **Semikolonseparerede værdier (CSV)**.
            4. Find `outlook_kalender.csv` og vælg din kalender som destination.
            """)
            
        with st.expander("🍏 Vejledning til Apple (iPhone & Mac)"):
            st.write("""
            **På iPhone:** Send filen `apple_kalender.ics` til dig selv i en besked eller mail. Tryk på filen og vælg **Tilføj alle**.
            
            **På Mac:** Åbn Kalender-appen. Gå til **Arkiv** > **Importér** og vælg `apple_kalender.ics`.
            """)
    else:
        st.error("Fejl i læsning af PDF.")
