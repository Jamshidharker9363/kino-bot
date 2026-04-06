from datetime import datetime

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.config import EXPORTS_DIR


def export_users_to_xlsx(users: list[dict]) -> str:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORTS_DIR / f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Users"
    headers = [
        "User ID",
        "Username",
        "Full Name",
        "Joined At",
        "Last Seen",
        "Message Count",
        "Requested Movies",
    ]
    sheet.append(headers)
    for user in users:
        sheet.append(
            [
                user.get("user_id", ""),
                user.get("username", ""),
                user.get("full_name", ""),
                user.get("joined_at", ""),
                user.get("last_seen_at", ""),
                user.get("message_count", 0),
                ", ".join(user.get("requested_movie_codes", [])),
            ]
        )
    for column in sheet.columns:
        length = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max(length + 2, 12), 40)
    workbook.save(path)
    return str(path)


def export_users_to_pdf(users: list[dict]) -> str:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORTS_DIR / f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "Bot users report")
    y -= 24
    pdf.setFont("Helvetica", 9)
    for user in users:
        text = (
            f"ID: {user.get('user_id')} | @{user.get('username', '')} | "
            f"{user.get('full_name', '')} | messages: {user.get('message_count', 0)} | "
            f"last seen: {user.get('last_seen_at', '')}"
        )
        y = _draw_wrapped_line(pdf, text, 40, y, width - 80, 11)
        y -= 6
        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            y = height - 40
    pdf.save()
    return str(path)


def _draw_wrapped_line(pdf, text: str, x: int, y: int, max_width: int, line_height: int) -> int:
    words = text.split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, "Helvetica", 9) <= max_width:
            line = candidate
        else:
            pdf.drawString(x, y, line)
            y -= line_height
            line = word
    if line:
        pdf.drawString(x, y, line)
    return y
