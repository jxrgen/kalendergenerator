import streamlit as st
import pandas as pd
import pdfplumber
from datetime import datetime
import io

def parse_pdf(file):
    all_events = []
    month_map = {
        "Marts": 3, "April": 4, "Maj": 5, "Juni": 6, "August": 8, 
        "September": 9, "Oktober": 10, "November": 11, "December": 12, 
        "Januar": 1, "Februar": 2
    }
    
    with pdfplumber.open(file) as pdf:
        table = pdf.pages[0].extract_table()
        if not table:
            return None
            
        for row in table[1:]: # Spring overskrift over
            if not row[0]: continue
            
            month_name = row[0].strip()
            month_num = month_map.get(month_name)
            if not month_num: continue
            
            # Bestem årstal (2026 for marts-dec, 2027 for jan-marts)
            year = 2026 if month_num >= 3 else 2027
            
            # Mødetyper og deres kolonne-index
            types = [
                ("Bogruppemøde", 2),
                ("Bestyrelsesmøde", 3),
                ("Månedsmøde", 4),
                ("Generalforsamling", 5)
            ]
            
            for title, idx in types:
                day_val = row[idx].replace('\n', '').strip() if row[idx] else ""
                if day_val and day_val.isdigit():
                    desc = f"Boggruppe {row[6].strip()} er vært" if idx >= 4 else ""
                    date_str = f"{month_num:02d}/{int(day_val):02d}/{year}"
                    all_events.append({
                        "Subject": title,
                        "Start Date": date_str,
                        "Start Time": "19:30",
                        "End Date": date_str,
                        "End Time": "22:00",
                        "All Day Event": "False",
                        "Description": desc,
                        "Location": "G/AIH",
                        "Private": "False"
                    })
    return pd.DataFrame(all_events)

st.set_page_config(page_title="G/AIH Kalender", page_icon="📅")
st.title("📅 G/AIH Kalender Generator")

uploaded_file = st.file_uploader("Upload kalender-PDF fra G/AIH", type="pdf")

if uploaded_file:
    df = parse_pdf(uploaded_file)
    if df is not None:
        st.success(f"Fundet {len(df)} møder!")
        st.dataframe(df)
        
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("Hent Google/Outlook CSV", csv, "kalender.csv", "text/csv")
        with col2:
            st.info("Tip: Importér CSV-filen direkte i din Google Kalender.")
    else:
        st.error("Kunne ikke læse tabellen i PDF'en. Tjek formatet.")
