from fpdf import FPDF
import pandas as pd
import datetime

def generate_player_report(df, team_name):
    pdf = FPDF()
    pdf.add_page()
    
    # --- INTESTAZIONE ---
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, f"MATCH REPORT: {team_name}", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generato il: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(5)

    # --- TOP SCORER ---
    if not df.empty:
        # Raggruppa per giocatore e somma i punti
        scorer_df = df.groupby('player')['punti'].sum().reset_index()
        top_player = scorer_df.loc[scorer_df['punti'].idxmax()]
        
        pdf.set_fill_color(255, 230, 0) # Giallo evidenziatore
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f" MVP DELLA SESSIONE: {top_player['player']} con {top_player['punti']} punti ", 1, 1, "C", True)
        pdf.ln(5)

    # --- FUNZIONE INTERNA PER DISEGNARE TABELLE ---
    def draw_team_table(pdf, data_df, t_name):
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(50, 50, 50)
        pdf.cell(0, 10, f" SQUADRA: {t_name}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        # Intestazioni
        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(230, 230, 230)
        cols = [("Giocatore", 50), ("2PT", 30), ("3PT", 30), ("TL", 30), ("Punti", 30)]
        for text, width in cols:
            pdf.cell(width, 8, text, 1, 0, "C", True)
        pdf.ln(8)

        # Dati Giocatori
        pdf.set_font("Arial", "", 9)
        players = data_df['player'].unique()
        for p in players:
            p_df = data_df[data_df['player'] == p]
            
            def fmt(tipo):
                sub = p_df[p_df['type'] == tipo]
                return f"{len(sub[sub['made']==True])}/{len(sub)}"

            pdf.cell(50, 8, p, 1)
            pdf.cell(30, 8, fmt("2PT"), 1, 0, "C")
            pdf.cell(30, 8, fmt("3PT"), 1, 0, "C")
            pdf.cell(30, 8, fmt("TL"), 1, 0, "C")
            pdf.cell(30, 8, str(p_df['punti'].sum()), 1, 1, "C")
        pdf.ln(5)

    # --- GENERAZIONE TABELLE ---
    # Tabella Squadra Principale
    draw_team_table(pdf, df[df['team'] == team_name], team_name)
    
    # Tabella Altre Squadre (Avversari)
    other_teams = [t for t in df['team'].unique() if t != team_name]
    for ot in other_teams:
        draw_team_table(pdf, df[df['team'] == ot], ot)

    return pdf.output(dest='S').encode('latin-1')
