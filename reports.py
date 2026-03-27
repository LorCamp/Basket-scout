from fpdf import FPDF
import pandas as pd
import datetime

def generate_player_report(df, team_name):
    pdf = FPDF()
    pdf.add_page()
    
    # --- INTESTAZIONE ---
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, f"SCOUTING REPORT: {team_name}", ln=True, align="C")
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, f"Data: {datetime.date.today().strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(10)

    # --- TABELLA RIASSUNTIVA PER GIOCATORE ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Statistiche Individuali", ln=True)
    pdf.ln(2)
    
    # Intestazioni Tabella
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(50, 8, "Giocatore", 1, 0, "C", True)
    pdf.cell(30, 8, "2PT", 1, 0, "C", True)
    pdf.cell(30, 8, "3PT", 1, 0, "C", True)
    pdf.cell(30, 8, "TL", 1, 0, "C", True)
    pdf.cell(30, 8, "Punti Tot", 1, 1, "C", True)

    pdf.set_font("Arial", "", 10)
    
    # Raggruppiamo i dati per giocatore
    players = df[df['team'] == team_name]['player'].unique()
    
    for p in players:
        p_df = df[df['player'] == p]
        
        # Calcolo percentuali
        def get_stat(type_str):
            sub = p_df[p_df['type'] == type_str]
            made = len(sub[sub['made'] == True])
            tot = len(sub)
            return f"{made}/{tot}"

        punti = p_df['punti'].sum()
        
        pdf.cell(50, 8, p, 1)
        pdf.cell(30, 8, get_stat("2PT"), 1, 0, "C")
        pdf.cell(30, 8, get_stat("3PT"), 1, 0, "C")
        pdf.cell(30, 8, get_stat("TL"), 1, 0, "C")
        pdf.cell(30, 8, str(punti), 1, 1, "C")

    # --- CONCLUSIONE ---
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Generato da Basket Scout PRO", align="R")

    return pdf.output(dest='S').encode('latin-1')
