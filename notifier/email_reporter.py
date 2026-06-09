import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from database.db import get_db_session
from database.models import Fund, FundStatus
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailReporter:
    def __init__(self):
        self.server = settings.SMTP_SERVER
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.to_email = settings.EMAIL_TO
        
    def _send_email(self, subject: str, html_content: str, text_content: str = None) -> None:
        if not self.username or not self.password or not self.to_email:
            import os
            from pathlib import Path
            logger.warning("Email credentials not configured. Printing report to console and saving to Desktop.")
            
            if text_content:
                print("\n" + "="*60)
                print(text_content)
                print("="*60)
            print("Email is not configured. Saving full HTML report to Desktop...")
            try:
                desktop = Path.home() / "Desktop"
                if desktop.exists():
                    file_path = desktop / f"MFScraper_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.html"
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    print(f"Report saved to: {file_path}")
                else:
                    print("Desktop folder not found. Skipping HTML file creation.")
            except Exception as e:
                logger.error(f"Failed to write report to Desktop: {e}")
            print("="*50 + "\n")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.username
        msg["To"] = self.to_email

        part = MIMEText(html_content, "html")
        msg.attach(part)

        try:
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            logger.info(f"Email sent successfully: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def generate_daily_report(self) -> None:
        """Generates and sends the daily ranked capacity report."""
        try:
            with get_db_session() as db:
                funds = db.query(Fund).filter(Fund.is_international == True).order_by(Fund.capacity_score.desc()).all()
                etfs = db.query(Fund).filter(Fund.ticker.isnot(None), Fund.premium_discount.isnot(None)).order_by(Fund.premium_discount.asc()).all()
                
                high_conviction = [f for f in funds if f.capacity_score >= 70]
                top_tracked = funds[:5] # Show top 5 regardless of score just for visibility
                
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                subject = f"International MF Capacity Tracker - {today}"
                
                html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>International MF Capacity Tracker</title>
                </head>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f7fa; margin: 0; padding: 20px; color: #333333;">
                    <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        
                        <!-- Header -->
                        <div style="background-color: #1a365d; color: #ffffff; padding: 30px 40px; text-align: center;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 0.5px;">International MF Capacity Tracker</h1>
                            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">Automated Intelligence Report • {today}</p>
                        </div>
                        
                        <!-- Body Content -->
                        <div style="padding: 40px;">
                """
                
                if not high_conviction:
                    html += """
                            <div style="background-color: #f8fafc; border-left: 4px solid #94a3b8; padding: 20px; border-radius: 4px; margin-bottom: 30px;">
                                <h3 style="margin: 0 0 10px 0; color: #475569; font-size: 16px;">System Status Update</h3>
                                <p style="margin: 0; color: #64748b; line-height: 1.5;">No high-conviction opportunities detected today. All tracked funds are currently scoring below the 70-point threshold. The agent will continue to monitor daily AUM drops and fund house notices.</p>
                            </div>
                    """
                else:
                    html += """
                            <h2 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px; font-size: 20px;">⚡ High Conviction Opportunities</h2>
                            <table style="width: 100%; border-collapse: collapse; margin-bottom: 40px;">
                                <thead>
                                    <tr style="background-color: #f1f5f9; text-align: left;">
                                        <th style="padding: 12px 15px; border-bottom: 2px solid #cbd5e1; color: #334155; font-weight: 600; font-size: 14px;">Fund Name</th>
                                        <th style="padding: 12px 15px; border-bottom: 2px solid #cbd5e1; color: #334155; font-weight: 600; font-size: 14px;">AMC</th>
                                        <th style="padding: 12px 15px; border-bottom: 2px solid #cbd5e1; color: #334155; font-weight: 600; font-size: 14px;">Score</th>
                                        <th style="padding: 12px 15px; border-bottom: 2px solid #cbd5e1; color: #334155; font-weight: 600; font-size: 14px;">Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                    """
                    for f in high_conviction:
                        action = "INVEST NOW" if f.capacity_score >= 90 else "WATCHLIST"
                        action_color = "#16a34a" if action == "INVEST NOW" else "#d97706"
                        bg_color = "#f0fdf4" if action == "INVEST NOW" else "#fffbeb"
                        
                        html += f"""
                                    <tr style="border-bottom: 1px solid #e2e8f0; transition: background-color 0.2s;">
                                        <td style="padding: 15px; color: #1e293b; font-size: 14px; font-weight: 500;">
                                            <a href="https://www.google.com/search?q={f.name.replace(' ', '+')}+mutual+fund" target="_blank" style="color: #2563eb; text-decoration: none;">{f.name}</a>
                                        </td>
                                        <td style="padding: 15px; color: #64748b; font-size: 14px;">{f.amc}</td>
                                        <td style="padding: 15px; color: #0f172a; font-size: 16px; font-weight: 700;">{f.capacity_score}</td>
                                        <td style="padding: 15px;">
                                            <span style="background-color: {bg_color}; color: {action_color}; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;">{action}</span>
                                        </td>
                                    </tr>
                        """
                    html += """
                                </tbody>
                            </table>
                    """
                    
                # Add ETF section
                if etfs:
                    html += """
                            <h2 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px; font-size: 18px; margin-top: 30px;">📈 Top International ETFs by Value</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="text-align: left;">
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">ETF Name</th>
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">Price</th>
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">NAV</th>
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">Prem/Disc %</th>
                                    </tr>
                                </thead>
                                <tbody>
                    """
                    for f in etfs:
                        pd_color = "#16a34a" if f.premium_discount <= 0 else "#dc2626"
                        pd_text = f"{f.premium_discount}%"
                        html += f"""
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="padding: 12px 15px; color: #475569; font-size: 13px;">
                                            <a href="https://www.google.com/search?q={f.ticker}+stock" target="_blank" style="color: #2563eb; text-decoration: none;">{f.name}</a>
                                        </td>
                                        <td style="padding: 12px 15px; color: #0f172a; font-size: 13px; font-weight: 600;">₹{f.latest_price}</td>
                                        <td style="padding: 12px 15px; color: #64748b; font-size: 13px;">₹{f.latest_nav}</td>
                                        <td style="padding: 12px 15px; color: {pd_color}; font-size: 13px; font-weight: 600;">{pd_text}</td>
                                    </tr>
                        """
                    html += """
                                </tbody>
                            </table>
                    """
                    
                # Add Top 5 section
                html += """
                            <h2 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px; font-size: 18px; margin-top: 30px;">📊 Top 5 Tracked Funds (Overview)</h2>
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="text-align: left;">
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">Fund Name</th>
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">Score</th>
                                        <th style="padding: 10px 15px; border-bottom: 1px solid #cbd5e1; color: #64748b; font-weight: 600; font-size: 13px;">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                """
                for f in top_tracked:
                    html += f"""
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="padding: 12px 15px; color: #475569; font-size: 13px;">
                                            <a href="https://www.google.com/search?q={f.name.replace(' ', '+')}+mutual+fund" target="_blank" style="color: #2563eb; text-decoration: none;">{f.name}</a>
                                        </td>
                                        <td style="padding: 12px 15px; color: #0f172a; font-size: 13px; font-weight: 600;">{f.capacity_score}</td>
                                        <td style="padding: 12px 15px; color: #64748b; font-size: 13px;">{f.current_status.value}</td>
                                    </tr>
                    """
                html += """
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- Footer -->
                        <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px; text-align: center;">
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">This is an automated intelligence report generated by the MFScraper Agent.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Generate Text Summary for Console Fallback
                text_summary = f"=== {subject} ===\n\n"
                if high_conviction:
                    text_summary += "⚡ HIGH CONVICTION OPPORTUNITIES:\n"
                    for f in high_conviction:
                        action = "INVEST NOW" if f.capacity_score >= 90 else "WATCHLIST"
                        text_summary += f"  - [{action}] {f.name} ({f.amc}) | Score: {f.capacity_score}\n"
                else:
                    text_summary += "ℹ️  System Status: No high-conviction opportunities today (all < 70).\n"
                    
                if etfs:
                    text_summary += "\n📈 TOP INTERNATIONAL ETFS BY VALUE:\n"
                    for f in etfs:
                        text_summary += f"  - {f.name} ({f.ticker}) | Price: ₹{f.latest_price} | NAV: ₹{f.latest_nav} | Prem/Disc: {f.premium_discount}%\n"
                    
                text_summary += "\n📊 TOP 5 TRACKED FUNDS:\n"
                for f in top_tracked:
                    text_summary += f"  - {f.name} | Score: {f.capacity_score} | Status: {f.current_status.value}\n"
                
                self._send_email(subject, html, text_content=text_summary)
                
        except Exception as e:
            logger.error(f"Error generating daily report: {e}", exc_info=True)
